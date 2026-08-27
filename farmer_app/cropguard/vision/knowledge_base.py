"""
Agronomic Knowledge Base: descriptions and precautions for recognized crop diseases.
"""

from typing import Dict, List, Any

DEFAULT_HEALTHY_ADVISORY = {
    "severity": "Low",
    "description": "No visible pathological lesions or fungal infections detected. The foliage shows healthy green pigmentation and vigor. Continue routine crop maintenance and scheduled scouting.",
    "precautions": [
        {
            "icon": "💧",
            "title": "Maintain Balanced Irrigation",
            "text": "Provide uniform soil moisture using drip or furrow irrigation. Avoid overhead splashing to minimize pathogen spore propagation."
        },
        {
            "icon": "🌱",
            "title": "Routine Field Scouting",
            "text": "Inspect lower leaves and shaded canopies weekly for early signs of fungal or bacterial spotting."
        },
        {
            "icon": "🧪",
            "title": "Preventive Soil Health",
            "text": "Ensure adequate potassium and micronutrient levels to support strong cell wall resistance against opportunistic pathogens."
        }
    ]
}

DEFAULT_UNKNOWN_ADVISORY = {
    "severity": "Medium",
    "description": "Symptoms observed require verification. Visual characteristics do not conclusively match known high-confidence disease signatures or image quality requires closer inspection.",
    "precautions": [
        {
            "icon": "📷",
            "title": "Retake Clear Close-Up",
            "text": "Capture a well-lit close-up photo focusing on the border between healthy and affected tissue."
        },
        {
            "icon": "🔍",
            "title": "Monitor Progression",
            "text": "Isolate the suspicious plant and check for spreading symptoms over 24-48 hours."
        },
        {
            "icon": "👨‍🌾",
            "title": "Consult Field Officer",
            "text": "Submit sample observation for review by a local agricultural extension officer."
        }
    ]
}

DISEASE_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "Apple Scab": {
        "severity": "High",
        "description": "Apple Scab is caused by the fungus Venturia inaequalis. It creates olive-green to black velvety spots on leaves and fruit, causing premature defoliation and fruit distortion.",
        "precautions": [
            {
                "icon": "✂️",
                "title": "Rake and Destroy Fallen Leaves",
                "text": "Infected leaves on the orchard floor harbor overwintering spores. Mulch or dispose of fallen leaves promptly."
            },
            {
                "icon": "💧",
                "title": "Apply Protective Fungicide",
                "text": "Spray sulfur or copper-based bio-fungicides during bud break and early vegetative growth before rain events."
            },
            {
                "icon": "🌬️",
                "title": "Prune for Air Circulation",
                "text": "Prune dense canopies to promote rapid drying of leaves after dew or rainfall."
            }
        ]
    },
    "Black Rot": {
        "severity": "High",
        "description": "Black Rot (Botryosphaeria obtusa) causes circular brown leaf spots ('frog-eye' leaf spot) and dark rot on fruit and cankers on branches.",
        "precautions": [
            {
                "icon": "✂️",
                "title": "Excise Cankers and Dead Wood",
                "text": "Prune out dead or infected branches at least 6 inches below visible margins and sterilize cutting tools."
            },
            {
                "icon": "🧴",
                "title": "Targeted Fungicide Spray",
                "text": "Apply captan or thiophanate-methyl according to local agronomic spray schedules."
            },
            {
                "icon": "🗑️",
                "title": "Remove Mummified Fruit",
                "text": "Strip any mummified fruit remaining on trees from the previous harvest to interrupt the fungal cycle."
            }
        ]
    },
    "Cedar Apple Rust": {
        "severity": "Medium",
        "description": "Cedar Apple Rust is caused by Gymnosporangium juniperi-virginianae. It produces bright yellow-orange spots on upper leaf surfaces that develop tube-like fungal structures beneath.",
        "precautions": [
            {
                "icon": "🌲",
                "title": "Manage Alternate Hosts",
                "text": "Remove eastern red cedar or juniper galls located within 100-200 meters of the orchard if possible."
            },
            {
                "icon": "💧",
                "title": "Apply Immunizing Sprays",
                "text": "Apply myclobutanil or mancozeb starting at pink bud stage through petal fall."
            },
            {
                "icon": "🌿",
                "title": "Plant Resistant Varieties",
                "text": "Consider rust-resistant cultivars (e.g., Enterprise, Liberty) for new plantings."
            }
        ]
    },
    "Powdery Mildew": {
        "severity": "Medium",
        "description": "Powdery Mildew appears as white or grayish powdery fungal patches on young leaves, shoots, and fruit, leading to leaf curling and stunted growth.",
        "precautions": [
            {
                "icon": "💧",
                "title": "Apply Potassium Bicarbonate / Sulfur",
                "text": "Spray organic potassium bicarbonate, neem oil formulation, or wettable sulfur in early morning or evening."
            },
            {
                "icon": "✂️",
                "title": "Prune Crowded Shoots",
                "text": "Improve sunlight penetration and air movement through selective pruning."
            },
            {
                "icon": "🌱",
                "title": "Avoid Excess Nitrogen",
                "text": "Reduce heavy nitrogen fertilization which stimulates overly succulent, susceptible new growth."
            }
        ]
    },
    "Cercospora Leaf Spot": {
        "severity": "Medium",
        "description": "Cercospora Leaf Spot / Gray Leaf Spot (Cercospora zeae-maydis) causes rectangular, grayish-brown lesions restricted by leaf veins on corn leaves, reducing photosynthetic area.",
        "precautions": [
            {
                "icon": "🔄",
                "title": "Crop Rotation",
                "text": "Rotate corn fields with non-host crops such as soybeans or legumes for at least one season."
            },
            {
                "icon": "🚜",
                "title": "Tillage and Residue Management",
                "text": "Incorporate crop residues into soil to accelerate breakdown of fungal inoculum."
            },
            {
                "icon": "💧",
                "title": "Foliar Fungicide Application",
                "text": "Apply strobilurin or triazole fungicides at tassel emergence if weather remains hot and humid."
            }
        ]
    },
    "Cercospora Leaf Spot / Gray Leaf Spot": {
        "severity": "Medium",
        "description": "Cercospora Leaf Spot / Gray Leaf Spot (Cercospora zeae-maydis) causes rectangular, grayish-brown lesions restricted by leaf veins on corn leaves, reducing photosynthetic area.",
        "precautions": [
            {
                "icon": "🔄",
                "title": "Crop Rotation",
                "text": "Rotate corn fields with non-host crops such as soybeans or legumes for at least one season."
            },
            {
                "icon": "🚜",
                "title": "Tillage and Residue Management",
                "text": "Incorporate crop residues into soil to accelerate breakdown of fungal inoculum."
            },
            {
                "icon": "💧",
                "title": "Foliar Fungicide Application",
                "text": "Apply strobilurin or triazole fungicides at tassel emergence if weather remains hot and humid."
            }
        ]
    },
    "Common Rust": {
        "severity": "Medium",
        "description": "Common Rust (Puccinia sorghi) produces golden-brown to dark brown powdery pustules on both upper and lower leaf surfaces of maize during moderate, humid weather.",
        "precautions": [
            {
                "icon": "💧",
                "title": "Targeted Fungicide Spray",
                "text": "Apply azoxystrobin or propiconazole if pustules spread to upper leaves prior to reproductive silking stage."
            },
            {
                "icon": "🌱",
                "title": "Select Resistant Hybrids",
                "text": "Utilize corn hybrids carrying specific Rp resistance genes suited for regional disease pressure."
            },
            {
                "icon": "📅",
                "title": "Early Planting",
                "text": "Plant early in the season to allow crops to mature before peak rust spore arrival."
            }
        ]
    },
    "Northern Leaf Blight": {
        "severity": "High",
        "description": "Northern Leaf Blight (Exserohilum turcicum) creates long, elliptical, grayish-green or tan cigar-shaped lesions on maize leaves, causing severe yield reduction if infection reaches ear leaves.",
        "precautions": [
            {
                "icon": "🧴",
                "title": "Timely Fungicide Spray",
                "text": "Apply fungicide before disease reaches the leaf below the ear during early reproductive stages."
            },
            {
                "icon": "🔄",
                "title": "Rotate Non-Host Crops",
                "text": "Rotate with pulses, oilseeds, or root crops for at least 1-2 seasons to decrease fungal load."
            },
            {
                "icon": "🌾",
                "title": "Residue Management",
                "text": "Bury infected corn stalks and debris to prevent primary spore dispersal at germination."
            }
        ]
    },
    "Early Blight": {
        "severity": "High",
        "description": "Early Blight (Alternaria solani) initiates dark brown to black spots with characteristic concentric rings ('target-board' pattern) primarily on older, lower foliage.",
        "precautions": [
            {
                "icon": "✂️",
                "title": "Prune Lower Foliage",
                "text": "Carefully remove infected lower leaves. Clean cutting tools between rows to prevent pathogen spread."
            },
            {
                "icon": "💧",
                "title": "Organic/Copper Fungicide",
                "text": "Spray copper-based organic fungicides or Bacillus subtilis thoroughly on both sides of remaining healthy leaves."
            },
            {
                "icon": "🌱",
                "title": "Switch to Drip Irrigation",
                "text": "Avoid overhead sprinkler watering to keep leaves dry. Apply straw or plastic mulch around the stem base."
            }
        ]
    },
    "Late Blight": {
        "severity": "High",
        "description": "Late Blight (Phytophthora infestans) is a destructive water-mold disease causing large, dark water-soaked lesions that rapidly turn black, with white fungal growth on the underside during humid weather.",
        "precautions": [
            {
                "icon": "⚠️",
                "title": "Immediate Preventive Spray",
                "text": "Apply systemic fungicides (mancozeb, chlorothalonil, or metalaxyl) immediately across the field."
            },
            {
                "icon": "🗑️",
                "title": "Destroy Severely Infected Plants",
                "text": "Bag and destroy heavily blighted plants away from the field to arrest airborne zoospore dispersal."
            },
            {
                "icon": "🌾",
                "title": "Avoid Wet Canopies",
                "text": "Do not irrigate in the evening. Increase row spacing to promote canopy aeration."
            }
        ]
    },
    "Bacterial Spot": {
        "severity": "High",
        "description": "Bacterial Spot (Xanthomonas spp.) causes small, dark, water-soaked angular spots on leaves and scabby raised spots on fruit.",
        "precautions": [
            {
                "icon": "🧴",
                "title": "Apply Copper-Mancozeb Mix",
                "text": "Apply a combination of copper bactericide and mancozeb for improved bacterial suppression."
            },
            {
                "icon": "🚫",
                "title": "Avoid Working in Wet Fields",
                "text": "Do not cultivate, harvest, or prune plants while foliage is wet to prevent bacterial inoculation."
            },
            {
                "icon": "💧",
                "title": "Drip Irrigation Only",
                "text": "Ensure no water is splashed from soil or adjacent leaves onto developing foliage."
            }
        ]
    }
}


def get_disease_advisory(disease_name: str, is_healthy: bool = False) -> Dict[str, Any]:
    """
    Retrieve descriptive agronomic advisory and precautions for a diagnosed disease.
    """
    if is_healthy or disease_name.lower() == "healthy":
        return DEFAULT_HEALTHY_ADVISORY.copy()

    # Direct match
    if disease_name in DISEASE_KNOWLEDGE_BASE:
        return DISEASE_KNOWLEDGE_BASE[disease_name].copy()

    # Case-insensitive partial match
    d_lower = disease_name.lower()
    for k, v in DISEASE_KNOWLEDGE_BASE.items():
        if k.lower() in d_lower or d_lower in k.lower():
            return v.copy()

    # Fallback
    advisory = DEFAULT_UNKNOWN_ADVISORY.copy()
    advisory["description"] = f"{disease_name} detected. " + advisory["description"]
    return advisory
