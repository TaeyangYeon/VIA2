"""Tests for pipeline_blocks.py — BlockDefinition registry and condition matching."""
import pytest
from agents.models import ImageDiagnosis
from agents.pipeline_blocks import (
    BlockDefinition,
    BLOCK_REGISTRY,
    get_matching_blocks,
    get_block,
    get_all_blocks,
    get_blocks_by_category,
)


def _diag(**kwargs) -> ImageDiagnosis:
    defaults = dict(
        contrast=0.0,
        noise_level=0.0,
        edge_density=0.0,
        lighting_uniformity=0.0,
        illumination_type="",
        noise_frequency="",
        reflection_level=0.0,
        surface_type="",
        depth_complexity=0.0,
        has_shadow_region=False,
        blob_feasibility=0.0,
        blob_count_estimate=0,
        color_discriminability=0.0,
        dominant_channel_ratio=0.0,
        structural_regularity=0.0,
        pattern_repetition=0.0,
        optimal_color_space="",
        threshold_candidate=0.0,
        edge_sharpness=0.0,
    )
    defaults.update(kwargs)
    return ImageDiagnosis(**defaults)


class TestBlockDefinitionStructure:
    def test_block_definition_has_name(self):
        block = get_block("grayscale")
        assert block is not None
        assert hasattr(block, "name")

    def test_block_definition_has_category(self):
        block = get_block("grayscale")
        assert hasattr(block, "category")

    def test_block_definition_has_when(self):
        block = get_block("grayscale")
        assert hasattr(block, "when")

    def test_block_definition_has_params(self):
        block = get_block("grayscale")
        assert hasattr(block, "params")

    def test_block_definition_has_description(self):
        block = get_block("grayscale")
        assert hasattr(block, "description")

    def test_name_is_string(self):
        block = get_block("grayscale")
        assert isinstance(block.name, str)

    def test_category_is_string(self):
        block = get_block("grayscale")
        assert isinstance(block.category, str)

    def test_params_is_dict(self):
        block = get_block("grayscale")
        assert isinstance(block.params, dict)

    def test_description_is_string(self):
        block = get_block("grayscale")
        assert isinstance(block.description, str)

    def test_when_is_callable(self):
        block = get_block("grayscale")
        assert callable(block.when)


class TestBlockRegistryCount:
    def test_total_block_count_is_26(self):
        # 5+6+4+7+4 = 26 (task spec listed "28" but individual blocks sum to 26)
        assert len(BLOCK_REGISTRY) == 26

    def test_get_all_blocks_returns_26(self):
        assert len(get_all_blocks()) == 26

    def test_color_space_count_is_5(self):
        assert len(get_blocks_by_category("color_space")) == 5

    def test_denoise_count_is_6(self):
        assert len(get_blocks_by_category("denoise")) == 6

    def test_threshold_count_is_4(self):
        assert len(get_blocks_by_category("threshold")) == 4

    def test_morphology_count_is_7(self):
        assert len(get_blocks_by_category("morphology")) == 7

    def test_edge_count_is_4(self):
        assert len(get_blocks_by_category("edge")) == 4


class TestGetBlockLookup:
    @pytest.mark.parametrize("name", [
        "grayscale", "hsv_s", "hsv_v", "lab_l", "ycrcb_cr",
        "gaussian_fine", "gaussian_mid", "bilateral", "median", "nlmeans", "clahe",
        "otsu", "adaptive_mean", "adaptive_gauss", "dynamic_threshold",
        "erosion", "dilation", "opening", "closing",
        "tophat", "blackhat", "morph_gradient",
        "canny", "sobel", "laplacian", "scharr",
    ])
    def test_get_block_exists(self, name):
        assert get_block(name) is not None

    def test_get_block_nonexistent_returns_none(self):
        assert get_block("nonexistent_block") is None

    def test_all_blocks_have_dict_params(self):
        for block in get_all_blocks():
            assert isinstance(block.params, dict), f"{block.name} params must be dict"

    def test_all_blocks_have_callable_when(self):
        for block in get_all_blocks():
            assert callable(block.when), f"{block.name} when must be callable"

    def test_all_blocks_when_accepts_image_diagnosis(self):
        d = _diag()
        for block in get_all_blocks():
            result = block.when(d)
            assert isinstance(result, bool), f"{block.name} when must return bool"


class TestConditionMatchingHighNoise:
    def test_gaussian_fine_matches_noise_above_5(self):
        d = _diag(noise_level=6.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "gaussian_fine" in names

    def test_gaussian_fine_not_matched_noise_below_5(self):
        d = _diag(noise_level=3.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "gaussian_fine" not in names

    def test_gaussian_mid_matches_noise_above_15(self):
        d = _diag(noise_level=20.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "gaussian_mid" in names

    def test_gaussian_mid_not_matched_noise_below_15(self):
        d = _diag(noise_level=10.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "gaussian_mid" not in names

    def test_bilateral_matches_noise_and_edge(self):
        d = _diag(noise_level=15.0, edge_sharpness=0.2)
        names = {b.name for b in get_matching_blocks(d)}
        assert "bilateral" in names

    def test_bilateral_not_matched_without_edge_sharpness(self):
        d = _diag(noise_level=15.0, edge_sharpness=0.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "bilateral" not in names

    def test_median_matches_noise_above_20(self):
        d = _diag(noise_level=25.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "median" in names

    def test_median_not_matched_noise_below_20(self):
        d = _diag(noise_level=15.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "median" not in names

    def test_nlmeans_matches_noise_above_30(self):
        d = _diag(noise_level=35.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "nlmeans" in names

    def test_nlmeans_not_matched_noise_below_30(self):
        d = _diag(noise_level=20.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "nlmeans" not in names

    def test_high_noise_matches_multiple_denoise_blocks(self):
        d = _diag(noise_level=35.0)
        names = {b.name for b in get_matching_blocks(d, category="denoise")}
        assert {"gaussian_fine", "gaussian_mid", "median", "nlmeans"}.issubset(names)


class TestConditionMatchingLighting:
    def test_clahe_matches_uneven_lighting(self):
        d = _diag(lighting_uniformity=0.3)
        names = {b.name for b in get_matching_blocks(d)}
        assert "clahe" in names

    def test_clahe_not_matched_low_uniformity(self):
        d = _diag(lighting_uniformity=0.1)
        names = {b.name for b in get_matching_blocks(d)}
        assert "clahe" not in names

    def test_adaptive_mean_matches_uneven_lighting(self):
        d = _diag(lighting_uniformity=0.25)
        names = {b.name for b in get_matching_blocks(d)}
        assert "adaptive_mean" in names

    def test_adaptive_gauss_matches_lighting_and_noise(self):
        d = _diag(lighting_uniformity=0.25, noise_level=15.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "adaptive_gauss" in names

    def test_adaptive_gauss_not_matched_low_noise(self):
        d = _diag(lighting_uniformity=0.25, noise_level=5.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "adaptive_gauss" not in names

    def test_tophat_matches_uneven_lighting(self):
        d = _diag(lighting_uniformity=0.35)
        names = {b.name for b in get_matching_blocks(d)}
        assert "tophat" in names

    def test_blackhat_matches_uneven_lighting(self):
        d = _diag(lighting_uniformity=0.35)
        names = {b.name for b in get_matching_blocks(d)}
        assert "blackhat" in names

    def test_lab_l_matches_uneven_lighting(self):
        d = _diag(lighting_uniformity=0.35)
        names = {b.name for b in get_matching_blocks(d)}
        assert "lab_l" in names

    def test_lab_l_not_matched_low_uniformity(self):
        d = _diag(lighting_uniformity=0.1)
        names = {b.name for b in get_matching_blocks(d)}
        assert "lab_l" not in names


class TestConditionMatchingContrast:
    def test_otsu_matches_high_contrast(self):
        d = _diag(contrast=0.2)
        names = {b.name for b in get_matching_blocks(d)}
        assert "otsu" in names

    def test_otsu_not_matched_low_contrast(self):
        d = _diag(contrast=0.1)
        names = {b.name for b in get_matching_blocks(d)}
        assert "otsu" not in names

    def test_dynamic_threshold_matches_low_contrast(self):
        d = _diag(contrast=0.1)
        names = {b.name for b in get_matching_blocks(d)}
        assert "dynamic_threshold" in names

    def test_dynamic_threshold_not_matched_high_contrast(self):
        d = _diag(contrast=0.2)
        names = {b.name for b in get_matching_blocks(d)}
        assert "dynamic_threshold" not in names


class TestConditionMatchingColor:
    def test_hsv_s_matches_color_discriminable(self):
        d = _diag(color_discriminability=0.4)
        names = {b.name for b in get_matching_blocks(d)}
        assert "hsv_s" in names

    def test_hsv_s_not_matched_low_discriminability(self):
        d = _diag(color_discriminability=0.2)
        names = {b.name for b in get_matching_blocks(d)}
        assert "hsv_s" not in names

    def test_hsv_v_matches_color_discriminable(self):
        d = _diag(color_discriminability=0.25)
        names = {b.name for b in get_matching_blocks(d)}
        assert "hsv_v" in names

    def test_hsv_v_not_matched_zero_discriminability(self):
        d = _diag(color_discriminability=0.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "hsv_v" not in names

    def test_ycrcb_cr_matches_color_and_balanced_channel(self):
        d = _diag(color_discriminability=0.5, dominant_channel_ratio=0.4)
        names = {b.name for b in get_matching_blocks(d)}
        assert "ycrcb_cr" in names

    def test_ycrcb_cr_not_matched_high_channel_ratio(self):
        d = _diag(color_discriminability=0.5, dominant_channel_ratio=0.6)
        names = {b.name for b in get_matching_blocks(d)}
        assert "ycrcb_cr" not in names

    def test_ycrcb_cr_not_matched_low_discriminability(self):
        d = _diag(color_discriminability=0.3, dominant_channel_ratio=0.4)
        names = {b.name for b in get_matching_blocks(d)}
        assert "ycrcb_cr" not in names


class TestConditionMatchingEdge:
    def test_canny_matches_sharp_edges(self):
        d = _diag(edge_sharpness=0.1)
        names = {b.name for b in get_matching_blocks(d)}
        assert "canny" in names

    def test_canny_not_matched_zero_sharpness(self):
        d = _diag(edge_sharpness=0.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "canny" not in names

    def test_sobel_matches_edges(self):
        d = _diag(edge_sharpness=0.05)
        names = {b.name for b in get_matching_blocks(d)}
        assert "sobel" in names

    def test_scharr_matches_edges(self):
        d = _diag(edge_sharpness=0.05)
        names = {b.name for b in get_matching_blocks(d)}
        assert "scharr" in names

    def test_laplacian_matches_sharp_low_noise(self):
        d = _diag(noise_level=5.0, edge_sharpness=0.1)
        names = {b.name for b in get_matching_blocks(d)}
        assert "laplacian" in names

    def test_laplacian_excluded_by_high_noise(self):
        d = _diag(noise_level=20.0, edge_sharpness=0.1)
        names = {b.name for b in get_matching_blocks(d)}
        assert "laplacian" not in names

    def test_laplacian_excluded_by_low_sharpness(self):
        d = _diag(noise_level=5.0, edge_sharpness=0.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "laplacian" not in names


class TestMorphologyConditions:
    def test_erosion_matches_high_edge_density(self):
        d = _diag(edge_density=0.15)
        names = {b.name for b in get_matching_blocks(d)}
        assert "erosion" in names

    def test_erosion_not_matched_low_edge_density(self):
        d = _diag(edge_density=0.05)
        names = {b.name for b in get_matching_blocks(d)}
        assert "erosion" not in names

    def test_dilation_matches_edge_density(self):
        d = _diag(edge_density=0.08)
        names = {b.name for b in get_matching_blocks(d)}
        assert "dilation" in names

    def test_opening_matches_noise(self):
        d = _diag(noise_level=15.0)
        names = {b.name for b in get_matching_blocks(d)}
        assert "opening" in names

    def test_closing_matches_edge_density(self):
        d = _diag(edge_density=0.08)
        names = {b.name for b in get_matching_blocks(d)}
        assert "closing" in names

    def test_morph_gradient_matches_high_edge_density(self):
        d = _diag(edge_density=0.15)
        names = {b.name for b in get_matching_blocks(d)}
        assert "morph_gradient" in names


class TestGetMatchingBlocksCategoryFilter:
    def test_filter_by_color_space_category(self):
        d = _diag()
        blocks = get_matching_blocks(d, category="color_space")
        assert all(b.category == "color_space" for b in blocks)

    def test_filter_by_denoise_category(self):
        d = _diag(noise_level=20.0)
        blocks = get_matching_blocks(d, category="denoise")
        assert all(b.category == "denoise" for b in blocks)

    def test_filter_by_edge_category(self):
        d = _diag(edge_sharpness=0.1)
        blocks = get_matching_blocks(d, category="edge")
        assert all(b.category == "edge" for b in blocks)

    def test_category_none_returns_multiple_categories(self):
        d = _diag(noise_level=20.0, contrast=0.2)
        blocks = get_matching_blocks(d, category=None)
        categories = {b.category for b in blocks}
        assert len(categories) > 1

    def test_unknown_category_returns_empty(self):
        d = _diag(noise_level=20.0)
        blocks = get_matching_blocks(d, category="unknown_category")
        assert blocks == []

    def test_get_blocks_by_category_returns_correct_names(self):
        color_blocks = {b.name for b in get_blocks_by_category("color_space")}
        assert color_blocks == {"grayscale", "hsv_s", "hsv_v", "lab_l", "ycrcb_cr"}


class TestDefaultDiagnosisMinimalMatching:
    def test_default_diagnosis_matches_grayscale(self):
        d = _diag()
        names = {b.name for b in get_matching_blocks(d)}
        assert "grayscale" in names

    def test_default_diagnosis_matches_dynamic_threshold(self):
        # contrast=0.0 < 0.15 so dynamic_threshold triggers
        d = _diag()
        names = {b.name for b in get_matching_blocks(d)}
        assert "dynamic_threshold" in names

    def test_default_diagnosis_no_denoise_blocks(self):
        d = _diag()
        names = {b.name for b in get_matching_blocks(d, category="denoise")}
        assert len(names) == 0

    def test_default_diagnosis_no_edge_blocks(self):
        d = _diag()
        names = {b.name for b in get_matching_blocks(d, category="edge")}
        assert len(names) == 0

    def test_default_diagnosis_no_morphology_blocks(self):
        d = _diag()
        names = {b.name for b in get_matching_blocks(d, category="morphology")}
        assert len(names) == 0
