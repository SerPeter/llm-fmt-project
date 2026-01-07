//! Token counting and estimation.
//!
//! This module provides token counting functionality for estimating
//! LLM token usage. It uses heuristic estimation that achieves ~94%
//! accuracy compared to actual tokenizers like tiktoken.

use std::sync::LazyLock;

use regex::Regex;

/// Common JSON/structured data token patterns (typically 1 token each).
static JSON_COMMON_TOKENS: LazyLock<std::collections::HashSet<&'static str>> =
    LazyLock::new(|| {
        [
            // 2-char patterns
            "{\"", "\"}", "\":", ",\"", "\",", ":[", "],", ":{", "},", "}]", "[{", "{{", "}}", "[[",
            "]]", "::", ",,", "[\"", "\"]", "..", "--", "==", // 3-char patterns
            "\":\"", "\"},", "\":[", "\"]}", "\"],", "\"}]", "}}}", "{{{", "]}}", "\":{", "...",
            "---", "===", ">>>", "<<<", // 4-char patterns
            "\":{\"", "\"},\"", "\"],[", "\":[\"", "\"]:\"",
        ]
        .into_iter()
        .collect()
    });

/// Regex for splitting text into segments.
static SEGMENT_PATTERN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(\s+|[^\s\w]+|\w+)").expect("Invalid regex"));

/// Regex for detecting CJK characters.
static CJK_PATTERN: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]")
        .expect("Invalid regex")
});

/// Regex for number-only segments.
static NUMBER_PATTERN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^\d+$").expect("Invalid regex"));

/// Regex for punctuation-only segments.
static PUNCTUATION_PATTERN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[^\w\s]+$").expect("Invalid regex"));

/// Default average characters per token for alphanumeric text.
pub const DEFAULT_CHARS_PER_TOKEN: f64 = 4.0;

/// Estimate token count using segment-based heuristics.
///
/// Uses tokenx-style analysis for ~94% accuracy compared to full tokenizers.
/// Based on <https://github.com/johannschopplich/tokenx> algorithm.
///
/// # Segment rules:
/// - Whitespace clusters: 0 tokens
/// - CJK characters: 1 token each
/// - Number sequences: 1 token
/// - Short segments (≤6 chars): 1 token
/// - Punctuation: uses common JSON pattern matching
/// - Alphanumeric: ceil(len / chars_per_token) tokens
#[must_use]
pub fn estimate_tokens(text: &str) -> usize {
    estimate_tokens_with_ratio(text, DEFAULT_CHARS_PER_TOKEN)
}

/// Estimate token count with a custom chars-per-token ratio.
#[must_use]
pub fn estimate_tokens_with_ratio(text: &str, chars_per_token: f64) -> usize {
    if text.is_empty() {
        return 0;
    }

    let mut tokens = 0usize;

    for cap in SEGMENT_PATTERN.captures_iter(text) {
        if let Some(segment) = cap.get(0) {
            tokens += estimate_segment_tokens(segment.as_str(), chars_per_token);
        }
    }

    tokens
}

/// Estimate tokens for a single segment.
fn estimate_segment_tokens(segment: &str, chars_per_token: f64) -> usize {
    // Whitespace: 0 tokens
    if segment.chars().all(char::is_whitespace) {
        return 0;
    }

    // CJK characters: 1 token each
    let cjk_count = CJK_PATTERN.find_iter(segment).count();
    if cjk_count > 0 {
        let non_cjk = segment.chars().count() - cjk_count;
        let non_cjk_tokens = if non_cjk > 0 {
            (non_cjk as f64 / chars_per_token).ceil() as usize
        } else {
            0
        };
        return cjk_count + non_cjk_tokens;
    }

    // Numbers: 1 token per sequence
    if NUMBER_PATTERN.is_match(segment) {
        return 1;
    }

    // Punctuation: check for common JSON patterns
    if PUNCTUATION_PATTERN.is_match(segment) {
        return estimate_punctuation_tokens(segment);
    }

    // Short alphanumeric segments: 1 token (common words up to ~6 chars)
    if segment.len() <= 6 {
        return 1;
    }

    // Long alphanumeric: ceil(len / chars_per_token)
    (segment.len() as f64 / chars_per_token).ceil() as usize
}

/// Estimate tokens for punctuation, accounting for common JSON patterns.
fn estimate_punctuation_tokens(segment: &str) -> usize {
    if segment.is_empty() {
        return 0;
    }

    // Check for exact common token matches
    if JSON_COMMON_TOKENS.contains(segment) {
        return 1;
    }

    // Try to greedily match common patterns
    let mut tokens = 0usize;
    let chars: Vec<char> = segment.chars().collect();
    let mut i = 0;

    while i < chars.len() {
        let mut matched = false;

        // Try longer patterns first (4, 3, then 2 chars)
        for length in [4, 3, 2] {
            if i + length <= chars.len() {
                let substr: String = chars[i..i + length].iter().collect();
                if JSON_COMMON_TOKENS.contains(substr.as_str()) {
                    tokens += 1;
                    i += length;
                    matched = true;
                    break;
                }
            }
        }

        if !matched {
            // Single punctuation char = 1 token
            tokens += 1;
            i += 1;
        }
    }

    tokens
}

/// Calculate token savings percentage.
#[must_use]
pub fn calculate_savings(original: usize, new: usize) -> f64 {
    if original == 0 {
        return 0.0;
    }
    ((original as f64 - new as f64) / original as f64) * 100.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_string() {
        assert_eq!(estimate_tokens(""), 0);
    }

    #[test]
    fn test_whitespace_only() {
        assert_eq!(estimate_tokens("   "), 0);
        assert_eq!(estimate_tokens("\n\t\n"), 0);
    }

    #[test]
    fn test_simple_words() {
        // Short words should be 1 token each
        let tokens = estimate_tokens("hello world");
        assert_eq!(tokens, 2);
    }

    #[test]
    fn test_longer_words() {
        // Longer words should use chars_per_token ratio
        let tokens = estimate_tokens("internationalization");
        assert!(tokens > 1);
    }

    #[test]
    fn test_numbers() {
        // Numbers should be 1 token
        assert_eq!(estimate_tokens("12345"), 1);
        assert_eq!(estimate_tokens("1 2 3"), 3);
    }

    #[test]
    fn test_json_structure() {
        let json = r#"{"name":"Alice","age":30}"#;
        let tokens = estimate_tokens(json);
        // Should recognize common JSON patterns
        assert!(tokens > 0);
        assert!(tokens < json.len()); // More efficient than 1 token per char
    }

    #[test]
    fn test_cjk_characters() {
        // CJK characters should be 1 token each
        let tokens = estimate_tokens("你好世界");
        assert_eq!(tokens, 4);
    }

    #[test]
    fn test_mixed_content() {
        let tokens = estimate_tokens("Hello 世界 123");
        assert!(tokens >= 4); // hello(1) + 世(1) + 界(1) + 123(1)
    }

    #[test]
    fn test_json_common_patterns() {
        // Common JSON patterns should be recognized
        assert_eq!(estimate_punctuation_tokens("{\""), 1);
        assert_eq!(estimate_punctuation_tokens("\"}"), 1);
        assert_eq!(estimate_punctuation_tokens("\":\""), 1);
    }

    #[test]
    fn test_calculate_savings() {
        assert!((calculate_savings(100, 50) - 50.0).abs() < 0.01);
        assert!((calculate_savings(100, 100) - 0.0).abs() < 0.01);
        assert_eq!(calculate_savings(0, 50), 0.0);
    }

    #[test]
    fn test_realistic_json() {
        let json = r#"[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]"#;
        let tokens = estimate_tokens(json);
        // Rough estimate: should be significantly less than character count
        assert!(tokens < json.len() / 2);
        assert!(tokens > 5); // At least a few tokens
    }
}
