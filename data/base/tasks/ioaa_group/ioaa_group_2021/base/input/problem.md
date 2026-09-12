# Team Competition 2021

Team Competition
Q1-1
English (Official)
Group Radio Astronomy (115 points)
Please read the general instructions in the separate envelope before you start this problem.
Measuring the Perseus arm using 21 cm HI line data
Context
Our goal here is to kinematically estimate the distance of (part of) the Perseus Arm of the Milky Way
(Figure 1), from the center of the Milky Way, based on the line-of-sight velocity of neutral hydrogen gas
via its 21 cm emission line.
Figure 1: Distance-galactic longitude map of the Milky Way arms
https://en.wikipedia.org/wiki/Perseus_Arm#/media/File:Milky_Way_Arms_ssc2008-10.svg

Team Competition
Q1-2
English (Official)
For this problem we will use a subset of the Canadian Galactic Plane Survey (CGPS, Figure 2), in which
individual radio telescope pointings can each yield the 21 cm line spectrum emitted by all the galactic
neutral hydrogen along the line of sight of the radio telescope.
Figure 2: Canadian galactic plane survey http://www.ras.ucalgary.ca/CGPS
By translating the Doppler wavelength shift of the 21 cm emission to a line-of-sight velocity, it is then
possible to identify individual emission components that correspond to distinct galactic arms. This iden-
tification allows for a reconstruction of the shape of each arm with respect to the Galactic Center.
In the spectrum corresponding to a radio telescope pointing, the Perseus arm can be readily identified
because it is often the brightest feature along each line of sight.
The frame of reference of the radio telescope observations can be taken to be the Sun, located at a
distance 𝑅0 from the Galactic Center (GC). The telescope has a pointing along a Line of Sight (LOS) defined
by a galactic longitude 𝑙 and a fixed galactic latitude 𝑏 = 0 . Along this LOS, the telescope picks up the
emission of a parcel of neutral H gas from the Perseus arm that is located at a distance 𝑟 from the Sun.
This same parcel of gas is located at a distance 𝑅 from the Galactic Center. Let us assume that both the
Sun and the gas parcel are in exact circular orbits around the GC. Additionally, it can be assumed that
both the Sun and the gas parcel are in the region where the rotation curve of the Milky Way is flat. The
measured (Doppler) velocity is denoted as v LOS, which equals to the velocity of the gas parcel along the
line of sight.

Team Competition
Q1-3
English (Official)
Data set
For this problem we attach a .csv file (21cmsurvey_full.csv, Excel and other spreadsheet software-
readable) which contain 21 cm HI line brightness temperature (𝑇𝑏) data vs. line-of-sight velocity (𝑉𝐿𝑂𝑆)
for a range of galactic longitudes (for galactic latitude = 0 ).
Row 1: Line-of-sight velocities 𝑣𝐿𝑂𝑆 (173 values, units: 𝑘𝑚𝑠−1).
Column 1 (after row 1): Galactic Longitude 𝑙 (1024 values, units: ∘).
Rows 2-1025: 21 cm HI Brightness Temperature 𝑇𝑏 (units: 𝐾). Each row yields the spectrum for the
pointing defined by 𝑙 (row name - column 1). There are thus 1024 spectra. Each spectrum has 173 𝑇𝑏
measurements, one for each 𝑣𝐿𝑂𝑆.
Part 1 (50 points).
1.1 Make a spectral plot of 𝑣𝐿𝑂𝑆 vs. 𝑇𝑏 for an adequate number of different values
(at least 20 plots) of galactic longitudes covering the full range of observations.
Identify the peak line of sight velocity of the Perseus gas parcel at each of the
plotted longitudes. Make sure to evenly sample the data set.
 
Note: Use the plot of the first or the last longitude as a guide to identify correct
peaks in the plots at the intermediate longitudes.
45.0pt
1.2 Why does the emission near 𝑣𝐿𝑂𝑆 = 0 (which we associate with our local arm)
have a lower brightness temperature than the emission from the Perseus arm?
5.0pt

Team Competition
Q1-4
English (Official)
Part 2 (20 points).
2.1 Derive an expression to calculate 𝑅 from 𝑣𝐿𝑂𝑆, 𝑣⊙, and 𝑙. You can assume:
• That both the Solar System and and the Perseus arm gas parcel along
the line of sight have a purely tangential velocity, with a negligible radial
component.
• A flat galactic rotation curve, i.e.
|v| = | v⊙|
where v is the velocity of the gas parcel.
20.0pt
Part 3 (20 points).
3.1 Using the 𝑣𝐿𝑂𝑆 values you found earlier, make a plot of galactic longitude 𝑙 vs.
𝑅 (radius with respect to the Galactic Center, in kpc) for the Perseus arm. Find
the average distance of the Perseus arm for the given longitude range. Also
report the standard deviation in your result. Use the values:
𝑣⊙ ≈ 225 𝑘𝑚𝑠 −1
𝑅0 ≈ 8 kpc
20.0pt
Part 4 (25 points).
4.1 The data also shows 21cm emission from the Norma arm of the Milky Way,
which is its outer arm. This emission is most clearly seen around the galactic
longitude of 145𝑜. Repeat the exercise for the Norma arm to find its distance
from GC. Use at least 5 data points to determine the distance of the Norma arm
from the Galactic Centre (at these galactic longitudes).
25.0pt
