"""LightingAdvisor — pure rule-based lighting recommendations from scene context."""


class LightingAdvisor:
    """Generates lighting recommendations based on image analysis results.

    All logic is rule-based; no LLM calls are made.
    """

    def generate_recommendations(self, scene_context: dict) -> list[dict]:
        """Return a list of lighting recommendation dicts.

        Each dict has keys: category, suggestion, reason, priority.
        Returns empty list when no issues are detected.
        """
        surface_type = scene_context.get("surface_type", "")
        reflection_level = scene_context.get("reflection_level", 0.0)
        lighting_uniformity = scene_context.get("lighting_uniformity", 1.0)
        illumination_type = scene_context.get("illumination_type", "")
        contrast = scene_context.get("contrast", 1.0)
        has_shadow_region = scene_context.get("has_shadow_region", False)
        noise_level = scene_context.get("noise_level", 0.0)

        recommendations = []

        if surface_type == "metal":
            recommendations.append({
                "category": "polarization",
                "suggestion": "Use cross-polarized lighting to eliminate specular glare",
                "reason": "Metal surfaces cause strong specular reflection",
                "priority": "high",
            })

        if reflection_level > 0.6:
            recommendations.append({
                "category": "light_shape",
                "suggestion": "Use diffuse dome or coaxial light source to reduce glare",
                "reason": "High reflection level detected; diffuse lighting reduces specular highlights",
                "priority": "high",
            })

        if lighting_uniformity < 0.5:
            recommendations.append({
                "category": "light_shape",
                "suggestion": "Use a uniform ring or dome light source",
                "reason": "Low lighting uniformity detected across the inspection area",
                "priority": "high",
            })

        if illumination_type == "spot":
            recommendations.append({
                "category": "light_type",
                "suggestion": "Use a wider-coverage light source to improve spatial uniformity",
                "reason": "Spot lighting creates uneven illumination across the inspection area",
                "priority": "medium",
            })

        if contrast < 0.3:
            recommendations.append({
                "category": "angle",
                "suggestion": "Adjust lighting angle or use coaxial illumination to improve contrast",
                "reason": "Low image contrast detected; directional or coaxial lighting can enhance edges",
                "priority": "medium",
            })

        if has_shadow_region:
            recommendations.append({
                "category": "light_type",
                "suggestion": "Use multi-angle or dome lighting to reduce shadow regions",
                "reason": "Shadow regions detected in the inspection image",
                "priority": "medium",
            })

        if noise_level > 0.3:
            recommendations.append({
                "category": "intensity",
                "suggestion": "Increase light intensity to improve the signal-to-noise ratio",
                "reason": "High noise level detected; brighter illumination raises SNR",
                "priority": "low",
            })

        return recommendations
