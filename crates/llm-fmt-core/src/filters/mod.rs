//! Data filters and transformations.
//!
//! This module provides filters for transforming data structures,
//! including depth limiting, path filtering, and truncation.

mod depth;
mod include;

pub use depth::MaxDepthFilter;
pub use include::IncludeFilter;

use std::fmt;

use crate::{Result, Value};

/// Trait for data filters.
pub trait Filter: Send + Sync {
    /// Apply the filter to a value.
    ///
    /// # Errors
    ///
    /// Returns an error if filtering fails.
    fn apply(&self, value: Value) -> Result<Value>;
}

/// A chain of filters applied in sequence.
#[derive(Default)]
pub struct FilterChain {
    filters: Vec<Box<dyn Filter>>,
}

impl fmt::Debug for FilterChain {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("FilterChain")
            .field("filters", &format!("[{} filters]", self.filters.len()))
            .finish()
    }
}

impl FilterChain {
    /// Create a new empty filter chain.
    #[must_use]
    pub fn new() -> Self {
        Self {
            filters: Vec::new(),
        }
    }

    /// Add a filter to the chain.
    pub fn add<F: Filter + 'static>(&mut self, filter: F) {
        self.filters.push(Box::new(filter));
    }

    /// Check if the chain is empty.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.filters.is_empty()
    }

    /// Get the number of filters in the chain.
    #[must_use]
    pub fn len(&self) -> usize {
        self.filters.len()
    }
}

impl Filter for FilterChain {
    fn apply(&self, mut value: Value) -> Result<Value> {
        for filter in &self.filters {
            value = filter.apply(value)?;
        }
        Ok(value)
    }
}
