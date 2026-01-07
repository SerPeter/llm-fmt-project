//! Pipeline orchestration for parse -> filter -> encode workflow.

use crate::encoders::{get_encoder, Encoder, ToonEncoder};
use crate::error::Error;
use crate::filters::{Filter, FilterChain};
use crate::parsers::{detect_parser, Parser};
use crate::Result;

/// Composable pipeline: parse -> filter -> encode.
pub struct Pipeline {
    parser: Box<dyn Parser>,
    encoder: Box<dyn Encoder>,
    filters: FilterChain,
}

impl Pipeline {
    /// Run the pipeline on input data.
    ///
    /// # Errors
    ///
    /// Returns an error if parsing, filtering, or encoding fails.
    pub fn run(&self, data: &[u8]) -> Result<String> {
        let parsed = self.parser.parse(data)?;
        let filtered = self.filters.apply(parsed)?;
        self.encoder.encode(&filtered)
    }
}

/// Builder for constructing pipelines.
#[derive(Default)]
pub struct PipelineBuilder {
    parser: Option<Box<dyn Parser>>,
    encoder: Option<Box<dyn Encoder>>,
    filters: FilterChain,
}

impl PipelineBuilder {
    /// Create a new pipeline builder.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Set the parser.
    #[must_use]
    pub fn with_parser<P: Parser + 'static>(mut self, parser: P) -> Self {
        self.parser = Some(Box::new(parser));
        self
    }

    /// Auto-detect and set parser based on filename or content.
    #[must_use]
    pub fn with_auto_parser(mut self, filename: Option<&str>, content: Option<&[u8]>) -> Self {
        self.parser = Some(detect_parser(filename, content));
        self
    }

    /// Set the encoder.
    #[must_use]
    pub fn with_encoder<E: Encoder + 'static>(mut self, encoder: E) -> Self {
        self.encoder = Some(Box::new(encoder));
        self
    }

    /// Set encoder by format name.
    ///
    /// # Errors
    ///
    /// Returns an error if the format is unknown.
    pub fn with_format(mut self, format: &str, sort_keys: bool) -> Result<Self> {
        self.encoder = Some(get_encoder(format, sort_keys)?);
        Ok(self)
    }

    /// Add a filter to the chain.
    #[must_use]
    pub fn add_filter<F: Filter + 'static>(mut self, filter: F) -> Self {
        self.filters.add(filter);
        self
    }

    /// Build the pipeline.
    ///
    /// # Errors
    ///
    /// Returns an error if the parser is not set.
    pub fn build(self) -> Result<Pipeline> {
        let parser = self.parser.ok_or_else(|| {
            Error::Pipeline("Parser not set. Use with_parser() or with_auto_parser().".into())
        })?;

        let encoder = self.encoder.unwrap_or_else(|| Box::new(ToonEncoder::new()));

        Ok(Pipeline {
            parser,
            encoder,
            filters: self.filters,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parsers::JsonParser;

    #[test]
    fn test_simple_pipeline() {
        let pipeline = PipelineBuilder::new()
            .with_parser(JsonParser)
            .build()
            .unwrap();

        let result = pipeline.run(br#"{"name": "test"}"#).unwrap();
        assert!(result.contains("name"));
        assert!(result.contains("test"));
    }

    #[test]
    fn test_pipeline_with_format() {
        let pipeline = PipelineBuilder::new()
            .with_parser(JsonParser)
            .with_format("json", false)
            .unwrap()
            .build()
            .unwrap();

        let result = pipeline.run(br#"{"a": 1}"#).unwrap();
        assert_eq!(result, r#"{"a":1}"#);
    }

    #[test]
    fn test_pipeline_missing_parser() {
        let result = PipelineBuilder::new().build();
        assert!(result.is_err());
    }

    #[test]
    fn test_tabular_data() {
        let pipeline = PipelineBuilder::new()
            .with_parser(JsonParser)
            .build()
            .unwrap();

        let input = br#"[{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]"#;
        let result = pipeline.run(input).unwrap();

        // Should produce tabular TOON format
        assert!(result.starts_with("@header:"));
    }
}
