# Perisomatic_Based_CellTyping
Repository to accompany the manuscript Perisomatic Ultrastructure Efficiently Classifies Cells in Mouse Cortex (Elabbady 2024). The tutorials in this repository are aimed to recapitulate the figures and analyses from the manuscript. 

Here we present how the perisomatic region of brain cells can be used to classify cells from a mm<sup>3</sup> volumetric electron microscopy dataset of mouse visual cortex. 
<p align="middle">
  <img src="./files/minnie_cut_v2.png" width="400" />
  <img src="./files/SomaCutout.png" width="250" /> 
</p>


## Installation

To run the tutorials provided in this repository please follow the detailed installation instructions found at [MicronsBinder](https://github.com/AllenInstitute/MicronsBinder). The conda environment file has been provided here as well.

Briefly, run the following:

```
conda env create -f environment.yml
conda activate micronsbinder
```

## Data Files

This repository comes with several public data files. Filenames and definitions are provided below:

### Dataset-wide files
  - microns_SomaData_AllCells_v661.pkl

This file contains the nucleus and soma features for all 94,010 cells presented in the manuscript. Note that this includes all predicted neurons and non-neurons but excludes any objects predicted as errors. The hierarchical model predictions for cell class and subclass are also included. Details about how each feature was calculated can be found in the Methods section under 'Generating Nucleus and Soma Features'. Note that the prediction provided match those presented in the manuscript. To access newer predictions or versions of the model, please query the cell-types table from the dataset directly using [CAVEClient](https://github.com/CAVEconnectome/CAVEclient). Instructions and tutorials on how to use CAVE can be found [here](https://caveconnectome.github.io/CAVEclient/).

  - inhibitory_perisomatic_feats_v661.pkl

This file contains the nucleus, soma, and PSS features that were extracted for all 6,805 predicted inhibitory neurons. Note that the numbers in each shape column denotes the number of objects of that shape detected within a given spatial bin. So for example, a value of 5 in shape_2_0_15000 means that a given cell had 5 instances of Shape 2 between 0-15 microns from the soma center point.

### Cortical Column files
The cortical column has been described in detail in Schneider-Mizell 2023 - this cells within this column have been proofread and with expert cell-type labels. The files below all aid in quantifying the truncation and completeness of cells within and outside the column.

  - column_edits_df.pkl
  - column_edit_distances.pkl

This file compiles all the proofreadings edits that were made for all the cells within the cortical column and notes the distance of each edit from the soma center point.

  - column_radial_truncation.pkl

This file contains the radial distance of each branch from the soma center point for each proofread cell within the cortical column.

  - column_syn_edits_df.pkl
  - nucleus_counts_perID_v661.pkl

## Other Resources
For accompanying feature extraction pipelines, please look at the following repositories:
- [Nucleus and Soma Extraction](https://github.com/lelabbady/Extract_Somatic_Features/tree/pipeline)
- [Spine Extraction](https://github.com/AllenInstitute/featureExtractionParty/) from mesh objects
- [Post-Synaptic Shape Feature Extraction](https://github.com/AllenInstitute/pss_extraction_pipeline)

To see how these features have enabled scientific discovery, please check out the following papers:
- Cell-type-specific inhibitory circuitry from a connectomic census of mouse visual cortex [(Schneider-Mizell 2023)](https://biorxiv.org/content/10.1101/2023.01.23.525290v3)
- The Synaptic Architecture of Layer 5 Thick Tufted Excitatory Neurons in the Visual Cortex of Mice [(Bodor 2023)](https://www.biorxiv.org/content/10.1101/2023.10.18.562531v1)
- Integrating EM and Patch-seq data: Synaptic connectivity and target specificity of predicted Sst transcriptomic types [(Gamlin 2023)](https://www.biorxiv.org/content/10.1101/2023.03.22.533857v1)
