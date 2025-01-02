import unittest
from project import extract_manga_id, safe_format_filename, is_valid_nhentai_xxx_url

class TestNhentaiDownloader(unittest.TestCase):
    def test_extract_manga_id(self):
        # Test valid URLs
        self.assertEqual(extract_manga_id("https://nhentai.xxx/g/123456/"), "123456")
        self.assertEqual(extract_manga_id("https://nhentai.xxx/g/123456"), "123456")
        self.assertEqual(extract_manga_id("nhentai.xxx/g/123456"), "123456")
        
        # Test URL with additional parameters
        self.assertEqual(extract_manga_id("https://nhentai.xxx/g/123456/?page=2"), "123456")
        
        # Test invalid URLs
        with self.assertRaises(ValueError):
            extract_manga_id("https://nhentai.xxx/invalid/url")
        with self.assertRaises(ValueError):
            extract_manga_id("https://nhentai.xxx/")

    def test_safe_format_filename(self):
        # Test normal strings
        self.assertEqual(safe_format_filename("normal name"), "normal name")
        self.assertEqual(safe_format_filename("name with spaces"), "name with spaces")
        
        # Test strings with invalid characters
        self.assertEqual(safe_format_filename('name/with\\invalid:chars*?'), 'namewithinvalidchars')
        
        # Test empty or None values
        self.assertEqual(safe_format_filename(""), "")
        self.assertEqual(safe_format_filename(None), "")
        
        # Test long filenames (should be truncated to 255 chars)
        long_name = "a" * 300
        self.assertEqual(len(safe_format_filename(long_name)), 255)

    def test_is_valid_nhentai_xxx_url(self):
        # Test valid URLs
        self.assertTrue(is_valid_nhentai_xxx_url("https://nhentai.xxx/g/123456/"))
        self.assertTrue(is_valid_nhentai_xxx_url("https://nhentai.xxx/g/123456"))
        
        # Test invalid URLs
        self.assertFalse(is_valid_nhentai_xxx_url("https://nhentai.net/g/123456/"))
        self.assertFalse(is_valid_nhentai_xxx_url("https://otherdomain.com/g/123456/"))
        self.assertFalse(is_valid_nhentai_xxx_url("invalid-url"))
        self.assertFalse(is_valid_nhentai_xxx_url(""))

if __name__ == '__main__':
    unittest.main()
