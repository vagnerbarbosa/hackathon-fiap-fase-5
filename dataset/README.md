---
license: mit
task_categories:
- object-detection
tags:
- yolo
- aws
- azure
- stride
- security
- threat-modeling
- computer-vision
---

# STRIDE Architecture Threat Modeling Dataset (AWS & Azure)

## 📌 Overview

This dataset was created to enable automatic STRIDE threat modeling from cloud architecture diagrams (AWS and Azure).

The goal is to detect architectural components in diagrams and support automated threat identification based on data flows and trust boundaries.

Annotations were created using Label Studio in YOLO format.

Total images: 4190  
Total classes: 32  

---

## 🎯 Purpose

- Detect cloud architecture components
- Identify trust boundaries
- Enable automated STRIDE threat analysis
- Support security research in diagram-based threat modeling

---

## 🖼 Image Source

Images were collected from publicly available architecture diagrams on the internet, including:

- AWS reference architectures
- Azure reference architectures
- Cloud solution blog posts
- Technical documentation examples

---

## 🔄 Data Augmentation Strategy

To improve robustness and simulate real-world variations, the following augmentations were applied:

- `_BW` (Black and White conversion)
- `_sharp` (Sharpen filter)
- `_contrast` (Contrast adjustment)
- `_gamma_hi` (High gamma correction)
- `_gamma_lo` (Low gamma correction)
- `_jpeg50` (JPEG compression 50%)
- `_blur1` (Gaussian blur level 1)
- `_noise6` (Noise injection level 6)
- `_degrade80` (Quality degradation 80%)

---

## 🏷 Classes (32 total)

| ID | Class |
|----|-------|
| 0 | actor_user |
| 1 | actor_admin |
| 2 | edge_ddos_protection |
| 3 | edge_cdn |
| 4 | edge_waf |
| 5 | edge_gateway |
| 6 | edge_portal |
| 7 | external_entry_point |
| 8 | integration_orchestrator |
| 9 | integration_messaging |
| 10 | compute_load_balancer |
| 11 | compute_service |
| 12 | compute_worker |
| 13 | data_database |
| 14 | data_cache |
| 15 | data_storage |
| 16 | security_identity_provider |
| 17 | security_key_management |
| 18 | obs_monitoring |
| 19 | obs_audit |
| 20 | external_backend_service |
| 21 | external_saas_service |
| 22 | external_web_service |
| 23 | communication_service |
| 24 | backup_service |
| 25 | boundary_cloud |
| 26 | boundary_region |
| 27 | boundary_resource_group |
| 28 | boundary_vpc_or_vnet |
| 29 | boundary_subnet_public |
| 30 | boundary_subnet_private |
| 31 | boundary_autoscaling_group |

---

## 📦 Dataset Format

YOLO format:

<class_id> <x_center> <y_center> <width> <height>

Values are normalized between 0 and 1.

---

## 🏗 Structure

train/images, val/images, test/images  
train/labels, val/labels, test/labels  
data.yaml

---

## 👤 Author

Guilherme Santos  
Vision Architecture Analyzer – 2026
