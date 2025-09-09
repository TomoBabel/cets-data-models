from cets_data_model.utils.image_utils import (
    get_image_dims,
    get_tiff_dims,
    get_mrc_dims,
    check_file_is_mrc,
    check_file_is_tif,
    get_image_info,
)
from tests.testing_tools import CetsDataModelTest


class UtilsTests(CetsDataModelTest):
    def test_get_image_dims_mrc(self):
        img = self.test_data / "mrc_stack.mrcs"
        assert get_image_dims(img) == (64, 64, 215)

    def test_get_image_dims_tiff(self):
        img = self.test_data / "single.tif"
        assert get_image_dims(img) == (32, 32, 1)

    def test_get_image_dims_bad_file(self):
        img = self.test_data / "null.txt"
        with self.assertRaises(ValueError):
            get_image_dims(img)

    def test_get_tiff_dims_stack(self):
        img = self.test_data / "tiff_stack.tiff"
        assert get_tiff_dims(img) == (78, 78, 24)

    def test_get_tiff_dims_2d(self):
        img = self.test_data / "single.tif"
        assert get_tiff_dims(img) == (32, 32, 1)

    def test_get_mrc_dims_2d(self):
        img = self.test_data / "single.mrc"
        assert get_mrc_dims(img) == (100, 100, 1)

    def test_get_mrc_dims_stack(self):
        img = self.test_data / "mrc_stack.mrcs"
        assert get_mrc_dims(img) == (64, 64, 215)

    def test_check_file_is_mrc(self):
        assert check_file_is_mrc(str(self.test_data / "mrc_stack.mrcs"))
        assert check_file_is_mrc(str(self.test_data / "single.mrc"))
        assert not check_file_is_mrc(str(self.test_data / "single.tif"))

    def test_check_file_is_tiff(self):
        assert not check_file_is_tif(str(self.test_data / "mrc_stack.mrcs"))
        assert not check_file_is_tif(str(self.test_data / "single.mrc"))
        assert check_file_is_tif(str(self.test_data / "single.tif"))

    def test_get_image_stats_mrc(self):
        img = self.test_data / "mrc_stack.mrcs"
        assert get_image_info(img).__dict__ == {
            "size_x": 64,
            "size_y": 64,
            "size_z": 215,
            "mode": "12",
            "mode_desc": "16-bit float (IEEE754)",
            "apix_x": 3.5399999618530273,
            "apix_y": 3.5399999618530273,
            "apix_z": 3.5399999618530273,
        }

    def test_get_image_stats_mrc_single(self):
        img = self.test_data / "single.mrc"
        assert get_image_info(img).__dict__ == {
            "size_x": 100,
            "size_y": 100,
            "size_z": 1,
            "mode": "2",
            "mode_desc": "32-bit signed real",
            "apix_x": 1.0499999237060547,
            "apix_y": 1.0499999237060547,
            "apix_z": None,
        }

    def test_get_image_stats_tiff(self):
        """Test tiff image doesn't contain pixel size in header, which is common"""
        img = self.test_data / "tiff_stack.tiff"
        assert get_image_info(img).__dict__ == {
            "size_x": 78,
            "size_y": 78,
            "size_z": 24,
            "mode": "I;16B",
            "mode_desc": "16-bit big endian unsigned integer pixels",
            "apix_x": None,
            "apix_y": None,
            "apix_z": None,
        }
