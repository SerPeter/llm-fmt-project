//! Truncation filters for limiting data size.
//!
//! This module provides filters for intelligently truncating data structures
//! to fit within size or token budgets while preserving the most relevant information.

use std::collections::HashSet;

use indexmap::IndexMap;
use rand::prelude::SliceRandom;
use rand::SeedableRng;

use crate::{Result, Value};

use super::Filter;

/// Strategy for selecting items when truncating arrays.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum TruncationStrategy {
    /// Keep the first N items.
    #[default]
    Head,
    /// Keep the last N items.
    Tail,
    /// Random sample of N items (uses fixed seed for reproducibility).
    Sample,
    /// Keep items from both start and end.
    Balanced,
}

impl TruncationStrategy {
    /// Parse a strategy from a string.
    ///
    /// # Errors
    ///
    /// Returns an error if the strategy name is unknown.
    pub fn from_str(s: &str) -> Result<Self> {
        match s.to_lowercase().as_str() {
            "head" => Ok(Self::Head),
            "tail" => Ok(Self::Tail),
            "sample" => Ok(Self::Sample),
            "balanced" => Ok(Self::Balanced),
            _ => Err(crate::Error::Filter(
                crate::error::FilterError::InvalidExpression(format!(
                    "Unknown truncation strategy: {s}. Valid options: head, tail, sample, balanced"
                )),
            )),
        }
    }
}

/// Summary of what was truncated.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct TruncationSummary {
    /// Number of arrays that were truncated.
    pub arrays_truncated: usize,
    /// Total number of items removed from arrays.
    pub items_removed: usize,
    /// Number of strings that were truncated.
    pub strings_truncated: usize,
    /// Total characters removed from strings.
    pub chars_removed: usize,
}

impl TruncationSummary {
    /// Create a new empty summary.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            arrays_truncated: 0,
            items_removed: 0,
            strings_truncated: 0,
            chars_removed: 0,
        }
    }

    /// Check if any truncation occurred.
    #[must_use]
    pub const fn was_truncated(&self) -> bool {
        self.arrays_truncated > 0 || self.strings_truncated > 0
    }

    /// Merge another summary into this one.
    pub fn merge(&mut self, other: &Self) {
        self.arrays_truncated += other.arrays_truncated;
        self.items_removed += other.items_removed;
        self.strings_truncated += other.strings_truncated;
        self.chars_removed += other.chars_removed;
    }
}

/// Filter that truncates data structures to fit within size limits.
#[derive(Debug, Clone)]
pub struct TruncationFilter {
    /// Maximum number of items per array.
    max_items: Option<usize>,
    /// Maximum length for string values.
    max_string_length: Option<usize>,
    /// Strategy for selecting items when truncating arrays.
    strategy: TruncationStrategy,
    /// Paths to preserve from truncation (JSON path syntax).
    preserve_paths: HashSet<String>,
    /// Suffix to append to truncated strings.
    truncation_suffix: String,
}

impl Default for TruncationFilter {
    fn default() -> Self {
        Self::new()
    }
}

impl TruncationFilter {
    /// Create a new truncation filter with default settings.
    #[must_use]
    pub fn new() -> Self {
        Self {
            max_items: None,
            max_string_length: None,
            strategy: TruncationStrategy::default(),
            preserve_paths: HashSet::new(),
            truncation_suffix: "...[truncated]".to_string(),
        }
    }

    /// Set the maximum number of items per array.
    #[must_use]
    pub const fn with_max_items(mut self, max_items: usize) -> Self {
        self.max_items = Some(max_items);
        self
    }

    /// Set the maximum length for string values.
    #[must_use]
    pub const fn with_max_string_length(mut self, max_length: usize) -> Self {
        self.max_string_length = Some(max_length);
        self
    }

    /// Set the truncation strategy.
    #[must_use]
    pub const fn with_strategy(mut self, strategy: TruncationStrategy) -> Self {
        self.strategy = strategy;
        self
    }

    /// Add a path to preserve from truncation.
    #[must_use]
    pub fn with_preserve_path(mut self, path: &str) -> Self {
        self.preserve_paths.insert(path.to_string());
        self
    }

    /// Add multiple paths to preserve from truncation.
    #[must_use]
    pub fn with_preserve_paths(mut self, paths: &[&str]) -> Self {
        for path in paths {
            self.preserve_paths.insert((*path).to_string());
        }
        self
    }

    /// Set the suffix appended to truncated strings.
    #[must_use]
    pub fn with_truncation_suffix(mut self, suffix: &str) -> Self {
        self.truncation_suffix = suffix.to_string();
        self
    }

    /// Apply truncation and return both the result and summary.
    pub fn apply_with_summary(&self, value: Value) -> Result<(Value, TruncationSummary)> {
        let mut summary = TruncationSummary::new();
        let result = self.truncate_value(value, "$", &mut summary);
        Ok((result, summary))
    }

    /// Recursively truncate a value.
    fn truncate_value(&self, value: Value, path: &str, summary: &mut TruncationSummary) -> Value {
        // Check if this path is preserved
        if self.is_preserved(path) {
            return value;
        }

        match value {
            Value::Object(obj) => {
                let truncated: IndexMap<String, Value> = obj
                    .into_iter()
                    .map(|(k, v)| {
                        let child_path = format!("{path}.{k}");
                        (k, self.truncate_value(v, &child_path, summary))
                    })
                    .collect();
                Value::Object(truncated)
            }
            Value::Array(arr) => {
                // First truncate the array length if needed
                let (truncated_arr, items_removed) = self.truncate_array(arr);
                if items_removed > 0 {
                    summary.arrays_truncated += 1;
                    summary.items_removed += items_removed;
                }

                // Then recursively truncate each item
                let result: Vec<Value> = truncated_arr
                    .into_iter()
                    .enumerate()
                    .map(|(i, v)| {
                        let child_path = format!("{path}[{i}]");
                        self.truncate_value(v, &child_path, summary)
                    })
                    .collect();
                Value::Array(result)
            }
            Value::String(s) => {
                if let Some((truncated, chars_removed)) = self.truncate_string(&s) {
                    summary.strings_truncated += 1;
                    summary.chars_removed += chars_removed;
                    Value::String(truncated)
                } else {
                    Value::String(s)
                }
            }
            other => other,
        }
    }

    /// Check if a path is preserved.
    fn is_preserved(&self, path: &str) -> bool {
        if self.preserve_paths.is_empty() {
            return false;
        }

        // Direct match
        if self.preserve_paths.contains(path) {
            return true;
        }

        // Check if any ancestor is preserved
        // For example, if $.metadata is preserved, $.metadata.id should also be preserved
        for preserved in &self.preserve_paths {
            if path.starts_with(preserved)
                && (path.len() == preserved.len()
                    || path.chars().nth(preserved.len()) == Some('.')
                    || path.chars().nth(preserved.len()) == Some('['))
            {
                return true;
            }
        }

        false
    }

    /// Truncate an array using the configured strategy.
    fn truncate_array(&self, arr: Vec<Value>) -> (Vec<Value>, usize) {
        let Some(max_items) = self.max_items else {
            return (arr, 0);
        };

        if arr.len() <= max_items {
            return (arr, 0);
        }

        let removed = arr.len() - max_items;

        let truncated = match self.strategy {
            TruncationStrategy::Head => arr.into_iter().take(max_items).collect(),
            TruncationStrategy::Tail => arr.into_iter().skip(removed).collect(),
            TruncationStrategy::Sample => {
                // Use a fixed seed for reproducibility in tests
                let mut rng = rand::rngs::StdRng::seed_from_u64(42);
                let mut indices: Vec<usize> = (0..arr.len()).collect();
                indices.shuffle(&mut rng);
                indices.truncate(max_items);
                indices.sort_unstable(); // Keep original order for sampled items
                indices
                    .into_iter()
                    .filter_map(|i| arr.get(i).cloned())
                    .collect()
            }
            TruncationStrategy::Balanced => {
                let half = max_items / 2;
                let remainder = max_items % 2;
                let tail: Vec<Value> = arr.iter().skip(arr.len() - half).cloned().collect();
                arr.iter()
                    .take(half + remainder)
                    .cloned()
                    .chain(tail)
                    .collect()
            }
        };

        (truncated, removed)
    }

    /// Truncate a string if it exceeds the max length.
    /// Returns Some((truncated_string, chars_removed)) if truncation was needed.
    fn truncate_string(&self, s: &str) -> Option<(String, usize)> {
        let max_length = self.max_string_length?;

        if s.len() <= max_length {
            return None;
        }

        let suffix_len = self.truncation_suffix.len();
        let truncate_at = if max_length > suffix_len {
            max_length - suffix_len
        } else {
            max_length
        };

        let truncated = if truncate_at > 0 && max_length > suffix_len {
            format!("{}{}", &s[..truncate_at], self.truncation_suffix)
        } else {
            s[..max_length].to_string()
        };

        let removed = s.len() - truncate_at;
        Some((truncated, removed))
    }
}

impl Filter for TruncationFilter {
    fn apply(&self, value: Value) -> Result<Value> {
        let (result, _summary) = self.apply_with_summary(value)?;
        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_truncate_array_head() {
        let filter = TruncationFilter::new().with_max_items(3);
        let arr = vec![
            Value::from(1),
            Value::from(2),
            Value::from(3),
            Value::from(4),
            Value::from(5),
        ];
        let (result, removed) = filter.truncate_array(arr);
        assert_eq!(result.len(), 3);
        assert_eq!(removed, 2);
        assert_eq!(result[0].as_number().unwrap().as_i64(), Some(1));
        assert_eq!(result[1].as_number().unwrap().as_i64(), Some(2));
        assert_eq!(result[2].as_number().unwrap().as_i64(), Some(3));
    }

    #[test]
    fn test_truncate_array_tail() {
        let filter = TruncationFilter::new()
            .with_max_items(3)
            .with_strategy(TruncationStrategy::Tail);
        let arr = vec![
            Value::from(1),
            Value::from(2),
            Value::from(3),
            Value::from(4),
            Value::from(5),
        ];
        let (result, removed) = filter.truncate_array(arr);
        assert_eq!(result.len(), 3);
        assert_eq!(removed, 2);
        assert_eq!(result[0].as_number().unwrap().as_i64(), Some(3));
        assert_eq!(result[1].as_number().unwrap().as_i64(), Some(4));
        assert_eq!(result[2].as_number().unwrap().as_i64(), Some(5));
    }

    #[test]
    fn test_truncate_array_balanced() {
        let filter = TruncationFilter::new()
            .with_max_items(4)
            .with_strategy(TruncationStrategy::Balanced);
        let arr = vec![
            Value::from(1),
            Value::from(2),
            Value::from(3),
            Value::from(4),
            Value::from(5),
            Value::from(6),
        ];
        let (result, removed) = filter.truncate_array(arr);
        assert_eq!(result.len(), 4);
        assert_eq!(removed, 2);
        // Balanced: 2 from start + 2 from end
        assert_eq!(result[0].as_number().unwrap().as_i64(), Some(1));
        assert_eq!(result[1].as_number().unwrap().as_i64(), Some(2));
        assert_eq!(result[2].as_number().unwrap().as_i64(), Some(5));
        assert_eq!(result[3].as_number().unwrap().as_i64(), Some(6));
    }

    #[test]
    fn test_truncate_array_sample() {
        let filter = TruncationFilter::new()
            .with_max_items(3)
            .with_strategy(TruncationStrategy::Sample);
        let arr = vec![
            Value::from(1),
            Value::from(2),
            Value::from(3),
            Value::from(4),
            Value::from(5),
        ];
        let (result, removed) = filter.truncate_array(arr);
        assert_eq!(result.len(), 3);
        assert_eq!(removed, 2);
        // Sample is deterministic with fixed seed, so we can check specific values
        // The sampled indices should be consistent across runs
    }

    #[test]
    fn test_truncate_string() {
        let filter = TruncationFilter::new().with_max_string_length(20);
        let s = "This is a very long string that needs truncation";
        let result = filter.truncate_string(s);
        assert!(result.is_some());
        let (truncated, removed) = result.unwrap();
        assert!(truncated.len() <= 20);
        assert!(truncated.ends_with("...[truncated]"));
        assert!(removed > 0);
    }

    #[test]
    fn test_no_truncation_needed() {
        let filter = TruncationFilter::new()
            .with_max_items(10)
            .with_max_string_length(100);
        let arr = vec![Value::from(1), Value::from(2), Value::from(3)];
        let (result, removed) = filter.truncate_array(arr);
        assert_eq!(result.len(), 3);
        assert_eq!(removed, 0);

        let s = "short string";
        assert!(filter.truncate_string(s).is_none());
    }

    #[test]
    fn test_nested_truncation() {
        let filter = TruncationFilter::new().with_max_items(2);

        let mut obj = IndexMap::new();
        obj.insert(
            "users".to_string(),
            Value::Array(vec![
                Value::from(1),
                Value::from(2),
                Value::from(3),
                Value::from(4),
            ]),
        );
        obj.insert(
            "logs".to_string(),
            Value::Array(vec![Value::from("a"), Value::from("b"), Value::from("c")]),
        );
        let data = Value::Object(obj);

        let (result, summary) = filter.apply_with_summary(data).unwrap();

        // Both arrays should be truncated to 2 items
        let users = result.get("users").unwrap().as_array().unwrap();
        assert_eq!(users.len(), 2);

        let logs = result.get("logs").unwrap().as_array().unwrap();
        assert_eq!(logs.len(), 2);

        assert_eq!(summary.arrays_truncated, 2);
        assert_eq!(summary.items_removed, 3); // 2 from users + 1 from logs
    }

    #[test]
    fn test_preserve_paths() {
        let filter = TruncationFilter::new()
            .with_max_items(1)
            .with_preserve_path("$.important");

        let mut obj = IndexMap::new();
        obj.insert(
            "important".to_string(),
            Value::Array(vec![Value::from(1), Value::from(2), Value::from(3)]),
        );
        obj.insert(
            "other".to_string(),
            Value::Array(vec![Value::from("a"), Value::from("b"), Value::from("c")]),
        );
        let data = Value::Object(obj);

        let (result, summary) = filter.apply_with_summary(data).unwrap();

        // "important" should be preserved (not truncated)
        let important = result.get("important").unwrap().as_array().unwrap();
        assert_eq!(important.len(), 3);

        // "other" should be truncated
        let other = result.get("other").unwrap().as_array().unwrap();
        assert_eq!(other.len(), 1);

        assert_eq!(summary.arrays_truncated, 1);
    }

    #[test]
    fn test_preserve_nested_path() {
        let filter = TruncationFilter::new()
            .with_max_string_length(5)
            .with_preserve_path("$.metadata");

        let mut metadata = IndexMap::new();
        metadata.insert(
            "description".to_string(),
            Value::from("this is a long description"),
        );

        let mut obj = IndexMap::new();
        obj.insert("metadata".to_string(), Value::Object(metadata));
        obj.insert("title".to_string(), Value::from("this is a long title"));
        let data = Value::Object(obj);

        let (result, summary) = filter.apply_with_summary(data).unwrap();

        // metadata.description should be preserved
        let desc = result.get("metadata").unwrap().get("description").unwrap();
        assert_eq!(desc.as_str().unwrap(), "this is a long description");

        // title should be truncated
        let title = result.get("title").unwrap().as_str().unwrap();
        assert!(title.len() <= 20); // max_length (5) < suffix length, so suffix is not added

        assert_eq!(summary.strings_truncated, 1);
    }

    #[test]
    fn test_strategy_from_str() {
        assert_eq!(
            TruncationStrategy::from_str("head").unwrap(),
            TruncationStrategy::Head
        );
        assert_eq!(
            TruncationStrategy::from_str("TAIL").unwrap(),
            TruncationStrategy::Tail
        );
        assert_eq!(
            TruncationStrategy::from_str("Sample").unwrap(),
            TruncationStrategy::Sample
        );
        assert_eq!(
            TruncationStrategy::from_str("balanced").unwrap(),
            TruncationStrategy::Balanced
        );
        assert!(TruncationStrategy::from_str("invalid").is_err());
    }

    #[test]
    fn test_summary_merge() {
        let mut s1 = TruncationSummary {
            arrays_truncated: 1,
            items_removed: 5,
            strings_truncated: 2,
            chars_removed: 100,
        };
        let s2 = TruncationSummary {
            arrays_truncated: 2,
            items_removed: 10,
            strings_truncated: 1,
            chars_removed: 50,
        };
        s1.merge(&s2);
        assert_eq!(s1.arrays_truncated, 3);
        assert_eq!(s1.items_removed, 15);
        assert_eq!(s1.strings_truncated, 3);
        assert_eq!(s1.chars_removed, 150);
    }

    #[test]
    fn test_filter_trait() {
        let filter = TruncationFilter::new().with_max_items(2);
        let arr = Value::Array(vec![Value::from(1), Value::from(2), Value::from(3)]);
        let result = filter.apply(arr).unwrap();
        assert_eq!(result.as_array().unwrap().len(), 2);
    }
}
