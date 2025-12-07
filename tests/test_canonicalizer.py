"""Unit tests for canonicalizer."""
import pytest
from canonicalizer import Canonicalizer


class TestCanonicalizer:
    """Tests for Canonicalizer class."""
    
    @pytest.fixture
    def canonicalizer(self):
        """Create canonicalizer instance."""
        return Canonicalizer()
    
    def test_federal_decree_law_canonicalization(self, canonicalizer):
        """Test Federal Decree-Law ID generation."""
        text = "Federal Decree-Law No. (47) of 2022 on Corporate Tax"
        canonical_id = canonicalizer.canonicalize_citation(text)
        
        assert canonical_id == "fed_decree_law_47_2022"
    
    def test_cabinet_resolution_canonicalization(self, canonicalizer):
        """Test Cabinet Resolution ID generation."""
        text = "Cabinet Resolution No. (37) of 2017"
        canonical_id = canonicalizer.canonicalize_citation(text)
        
        assert canonical_id == "cabinet_resolution_37_2017"
    
    def test_federal_law_canonicalization(self, canonicalizer):
        """Test Federal Law ID generation."""
        text = "Federal Law No. (5) of 1985 promulgating the Civil Code"
        canonical_id = canonicalizer.canonicalize_citation(text)
        
        assert canonical_id == "federal_law_5_1985"
    
    def test_normalize_term(self, canonicalizer):
        """Test term normalization."""
        term = "  Ministry:  "
        normalized = canonicalizer.normalize_term(term)
        
        assert normalized == "Ministry"
        assert not normalized.endswith(':')
    
    def test_normalize_definition(self, canonicalizer):
        """Test definition normalization."""
        definition = "  Ministry of Finance.  "
        normalized = canonicalizer.normalize_definition(definition)
        
        assert normalized == "Ministry of Finance."
        assert not normalized.startswith(' ')
        assert not normalized.endswith(' ')
    
    def test_handle_variations(self, canonicalizer):
        """Test handling of citation variations."""
        variations = [
            "Federal Decree-Law No. (47) of 2022",
            "Federal Decree Law No. 47 of 2022",
            "Federal Decree by Law No. (47) of 2022"
        ]
        
        canonical_ids = [canonicalizer.canonicalize_citation(v) for v in variations]
        
        # All should normalize to same ID
        assert all(cid == "fed_decree_law_47_2022" for cid in canonical_ids)
