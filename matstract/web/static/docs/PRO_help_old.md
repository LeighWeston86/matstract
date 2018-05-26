##### Property

# Do we want to include device properties, or just intrinsic materials properties?

###### Part of speech: NN, NP

Definition (i): anything measurable that can have a unit and a value, e.g., conductivity, band gap, or quantities based on many values e.g., band structure. Does not included conditions such as temperature, or sample specific properties such as
thickness. Does not have to be a property of a material, can be a property of a device. This will be taken care of later by relation annotation.

i. "We measured the (`electron mobility`, NP) of GaN to be 10 cm$^2$/Vs"

ii. The (`band gap`, NP) of ZnO is 3.4 eV

iii. We calculated the (`band structure`, NP) using tight binding

iv. The (`yield`, NN) of the reaction was 80%.

&nbsp;

Definition (ii): Any binary property or phenomenon exhibited by a material, usually in relative terms e.g.,
ferroelectricity, metallic.

i. BaTiO3 exhibits (`ferroelectricity`, NN)

ii. We studied (`metallic`, JJ) Ge nanowires

iii. The sample was (`stiff`, JJ)

iv. (`Silicon doped`, VB) ZnO

v. (`p-type`) GaAs

&nbsp;

Definition (iii): Any measureable spectra, e.g., `absorption spectrum`, `phonon dispersion curve`

&nbsp;

Definition (iv): Properties that include another species, e.g., `adsorption isotherm`, `band offset`, or, properties that depend on a device, e.g., `leakage current`, are not materials properties, but will be included to improve the NLP models.

&nbsp;

Definition (v): Growth directions and crystal orientations

i. predominant (`orientation`, PRO) (`along (311) plane`, PVL)
