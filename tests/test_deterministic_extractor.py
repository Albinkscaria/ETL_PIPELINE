"""Unit tests for deterministic extractor."""
import pytest
from models import Page
from deterministic_extractor import DeterministicExtractor


class TestDeterministicExtractor:
    """Tests for DeterministicExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return DeterministicExtractor()
    
    def test_citation_extraction_basic(self, extractor):
        """Test basic citation pattern extraction."""
        text = "Federal Decree-Law No. (47) of 2022 on Corporate Tax"
        page = Page(page_num=1, text=text, layout_info={})
        
        citations = extractor.extract_citations([page])
        
        assert len(citations) > 0
        assert "47" in citations[0].text
        assert "2022" in citations[0].text
    
    def test_citation_with_amendment(self, extractor):
        """Test citation with 'as amended' clause."""
        text = "Federal Decree-Law No. (7) of 2017 on Excise Tax, as amended"
        page = Page(page_num=1, text=text, layout_info={})
        
        citations = extractor.extract_citations([page])
        
        assert len(citations) > 0
        assert "as amended" in citations[0].text.lower()
    
    def test_cabinet_resolution_pattern(self, extractor):
        """Test Cabinet Resolution pattern."""
        text = "Cabinet Resolution No. (37) of 2017 Concerning Executive Regulations"
        page = Page(page_num=1, text=text, layout_info={})
        
        citations = extractor.extract_citations([page])
        
        assert len(citations) > 0
        assert "37" in citations[0].text
        assert "2017" in citations[0].text
    
    def test_definition_colon_pattern(self, extractor):
        """Test 'Term: Definition' extraction."""
        text = """
        Article (1) - Definitions
        
        Ministry: Ministry of Finance.
        Authority: Federal Tax Authority.
        """
        page = Page(page_num=2, text=text, layout_info={})
        
        definitions = extractor.extract_definitions([page])
        
        # Should extract at least one definition
        assert len(definitions) > 0
        
        # Check if Ministry or Authority was extracted
        terms = [d.term for d in definitions]
        assert any('Ministry' in t or 'Authority' in t for t in terms)
    
    def test_confidence_scoring(self, extractor):
        """Test confidence score calculation."""
        text = "Federal Decree-Law No. (47) of 2022 on Corporate Tax"
        page = Page(page_num=1, text=text, layout_info={})
        
        citations = extractor.extract_citations([page])
        
        assert len(citations) > 0
        assert 0.0 <= citations[0].confidence <= 1.0
        assert citations[0].confidence > 0.8  # Should be high confidence
    
    def test_no_false_positives(self, extractor):
        """Test that random text doesn't produce citations."""
        text = "This is just regular text with no legal citations."
        page = Page(page_num=1, text=text, layout_info={})
        
        citations = extractor.extract_citations([page])
        
        assert len(citations) == 0
    
    def test_multiple_citations_same_page(self, extractor):
        """Test extracting multiple citations from same page."""
        text = """
        Having reviewed:
        - Federal Decree-Law No. (7) of 2017 on Excise Tax;
        - Federal Decree-Law No. (8) of 2017 on Value Added Tax;
        - Federal Decree-Law No. (32) of 2021 on Commercial Companies;
        """
        page = Page(page_num=1, text=text, layout_info={})
        
        citations = extractor.extract_citations([page])
        
        assert len(citations) >= 3
