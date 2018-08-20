##### Material of interest

###### Part of speech: NN, NP, JJ

Any inorganic solid or alloy, any non-gaseous element (at RT), e.g., BaTiO3, FeNi, Fe. 

i. This study focuses on (`BaTiO3`, NN) thin films

ii. The aspect ratio of the (`carbon nanotubes`, NP) (not strictly inorganic, but we make an exception for carbon)

iii. The (`Ni`, JJ) catalyst had high effieciency.

If it is a mixture of materials, make sure to annotate hyphens and slashes, so it is treated as a single entity. If it is a heterostructure, i.e. materials are not mixed, annotated them as separate materials.

iv. Fabrication and characterization of (`B2O3–Al2O3–Na2O`, NN) glass system.

v. (`GaN` / `ZnO`, NN, NN) heterostructure was used for LEDs.

Notes:

Do not annotate ions: Li is ok, Li+ is not.

Ion is ok in the case of doping: `ZnO:Li+`

Material classes are also acceptable: `metal chalcogenides`

Do not mark elemetns that are not metals or metaloids, e.g., F, Cl etc.

Hyphens in composites and alloys:

highlight the hypen in alloys (it's a single material): `Ni-Fe` alloy

Don't highlight for composite/heterostructure (distinct materials): `Ni`-`Fe` composite

Very often due to tokenization error the plane of a material is included, e.g., Si(100). If it is included, hihglight the whole thing as a MAT:
`Si(100)`, if tokenization is correct, highlight Si separately: `Si` (100).

When to include the stoichiometry range:

Good: We studied `ABO3 where A = Ba, Sr; B = Zr, Ti`

Here the where can be where, with, nothing, etc.

If there is too many words between,

Bad: `ABO3 where we have used A = Ba, Sr; B = Zr, Ti`

Then don't highlight the whole thing. Just highlight ABO3 and the individual sibstitutions.

Metal and Oxide:

Correct:

`metal` - `oxide` interface
Properties of the `metal oxide`
