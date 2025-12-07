# **Q-SPI: Integrating Technical Debt into Earned Value Management**

This repository contains the source code, simulation scripts, and anonymized datasets for the paper **"Q-SPI: Integrating Technical Debt into Earned Value Management via the Quality-Adjusted SPI"**.

## **📖 Overview**

Traditional Earned Value Management (EVM) metrics like the Schedule Performance Index (SPI) are often "quality-blind," rewarding velocity even when it is achieved by accumulating Technical Debt (TD).

**Q-SPI** introduces a mathematical framework to penalize the Earned Value (EV) based on the remediation cost of accumulated debt, using an exponential decay function:

$$Q\\text{-}SPI \= SPI \\times e^{-\\lambda \\left( \\frac{TD\_{new}}{\\beta \\cdot EV\_{raw}} \\right)}$$  
This repository provides the tools to reproduce the paper's findings, specifically the "Technical Bankruptcy" event observed in the BioArc case study and the sensitivity analysis of the $\\lambda$ parameter.

## **📂 Reproducibility & Audit Trail**

To ensure transparency and allow for independent verification of our results, we provide the following **anonymized datasets** corresponding to the case studies presented in the manuscript.

### **1\. BioArc Case Study (Section 4.1)**

The following files in data/audit\_trail/ substantiate the "Illusion of Progress" (Sprints 4-6) and the subsequent crash (Sprint 7\) reported in **Table 3** and **Figure 4**.

| File Name | Description | Corresponds To |
| :---- | :---- | :---- |
| **bioarc\_sprint\_metrics\_anonymized.csv** | Raw velocity logs exported from the project management tool (Mizito). It demonstrates the high velocity during the "OTP Rush" and the subsequent drop to zero during the refactoring halt. | **Table 3** (Rows: SPI vs Q-SPI) |
| **sonarqube\_debt\_timeline.csv** | Historical extraction of Technical Debt (SQALE rating) and code smells. It validates the spike in debt accumulation (35h $\\to$ 100h) due to architectural erosion. | **Figure 4** (Divergence point) |
| **git\_commit\_audit\_trail.txt** | A summary of critical git commit messages (anonymized authors). It provides qualitative evidence of the "hacking" culture and architectural erosion (e.g., God Class growth) during the crisis phase. | **Section 4.1.3** |

### **🔒 Data Privacy Statement**

*Original datasets contained sensitive information regarding patient records (HIPAA-protected) and developer identities. All personal identifiers (PII) have been hashed or removed. Project timestamps, metric values (Story Points, Hours), and structural code metrics remain unaltered to preserve statistical integrity.*

## **📊 Sensitivity Analysis (Robustness Check)**

To address concerns regarding the calibration of the sensitivity coefficient ($\\lambda$), we provide a script to perform a numerical sensitivity analysis (**Section 5.2**).

### **How to Run**

1. **Install Dependencies:**  
```
   pip install numpy matplotlib pandas seaborn
```

2. **Execute the Script:**  
```
   python scripts/sensitivity_analysis.py
```

3. **Output:**  
   * **sensitivity\_analysis.pdf**: A high-resolution vector plot corresponding to **Figure 6** in the revised manuscript.  
   * **Console Output**: A numerical table showing the volatility of Q-SPI ($\<1.5\\%$ in low-debt regimes vs. $\\sim9\\%$ in crisis regimes).

## **📁 Repository Structure**

```
Q-SPI/  
├── data/  
│   └── audit_trail/               \# Anonymized evidence for reviewers  
│       ├── bioarc_sprint_metrics_anonymized.csv  
│       ├── sonarqube_debt_timeline.csv  
│       └── git_commit_audit_trail.txt   
├── scripts/  
│   ├── calculate_qspi.py          \# Core logic for Q-SPI calculation  
│   └── sensitivity_analysis.py    \# Robustness check script  
├── results/                       \# Generated figures and tables  
└── README.md                      \# This file  
```

## **🔗 Citation**

If you use this model or dataset in your research, please cite:

Tanhaei, M. "Q-SPI: Integrating Technical Debt into Earned Value Management via the Quality-Adjusted SPI".

*(BibTeX will be updated upon publication)*

### **Contact**

For questions regarding the dataset or the Q-SPI implementation, please open an issue in this repository or contact the corresponding author at m.tanhaei@ilam.ac.ir.