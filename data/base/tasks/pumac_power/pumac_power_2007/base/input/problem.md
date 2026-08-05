# PUMaC Power Round 2007

PUMaC 2007 Power Test: Lattices
A real n-dimensional lattice Λ is a set of n-tuples ( a1, a2, . . . , an) of real numbers with the
following properties:
1) The all-zero-tuple 0 = (0, 0, . . . ,0) belongs to Λ.
2) If u = (a1, a2, . . . , an) and v = (b1, b2, . . . , bn) belong to Λ, then so do−u = (−a1,−a2, . . . ,−an)
and u + v = (a1 + b1, a2 + b2, . . . , an + bn).
For example, the set Z2 of ordered pairs of integers forms a lattice, as does the trivial n-
dimensional lattice, which consists of the single n-tuple 0.
The distance between two n-tuples ( a1, a2, . . . , an) and ( b1, b2, . . . , bn) in a lattice Λ is the
standard Euclidean distance
√
(b1− a1)2 + (b2− a2)2 + . . . + (bn− an)2.
Given a lattice Λ, we refer to its elements as either points, or the vectors they represent.
For the problems below, show all your work and give justiﬁcation for all answers, unless other-
wise indicated. Answers given without justiﬁcation will not be given full credit.
1 Minimal Vectors
The minimal vectors of a lattice are the ones (other than the 0 vector) represented by the points
closest to the origin, 0. The norm of a minimal vector is the square of the distance from the point
that represents it to the origin. The norm of a minimal vector of a lattice is called the minimal
norm of that lattice. In Z2, the minimal vectors are (1 , 0), (0, 1), (−1, 0), and (0 ,−1).
a) How many minimal vectors are there in the 1-dimensional lattice Z1?
b) How many minimal vectors are there in the 3-dimensional lattice Z3?
c) Given any integer m, how many minimal vectors are there in the m-dimensional lattice Zm?
1
The checkerboard lattice Dn is the set of all points in Zn for which the sum of all n coordinates
is even.
d) How many minimal vectors are there in D3?
e) Given any integer m, how many minimal vectors are there in Dm?
2 Bases
Consider the lattice Z3. We can ﬁnd three vectors v1, v2, v3 such that any vector in Z3 may be
expressed in the form
3∑
i=1
kivi, where k1, k2, k3 are integers. The vectors v1, v2, v3 are then called
a basis for the lattice Z3. The vectors (1 , 0, 0), (0 , 1, 0), and (0 , 0, 1) form a basis for Z3, because
any vector ( a, b, c)∈ Z3 can be expressed as ( a, b, c) = a(1, 0, 0) + b(0, 1, 0) + c(0, 0, 1), and the
coeﬃcents a, b, and c are integers.
a) Give a basis for Zm.
b) Give a basis for Dm.
c) Consider the 8-dimensional lattice with basis vectors
(2, 0, 0, 0, 0, 0, 0, 0),
(−1, 1, 0, 0, 0, 0, 0, 0),
(0, −1, 1, 0, 0, 0, 0, 0),
(0, 0, −1, 1, 0, 0, 0, 0),
(0, 0, 0, −1, 1, 0, 0, 0),
(0, 0, 0, 0, −1, 1, 0, 0),
(0, 0, 0, 0, 0, −1, 1, 0),
(1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2).
Which points can be in this lattice, what is the minimal norm, and how many minimal vectors are
there?
The lattice given in part (c) is called the E8 diamond lattice.
d) Prove that we can describe the lattice Z3 with D3 as follows: Z3 consists of all points in
D3 and all points which are obtained by adding the vector (1 , 1, 1) to a point in D3. (We shall
denote this by Z3 = D3∪ (D3 + (1, 1, 1)).)
e) Give a similar description of E8 in terms of D8.
2
3 Sphere Packings
Lattices can be useful for describing sphere packings , the classical problem of ﬁnding how
densely a large number of identical spheres can be packed together, wasting as little space as
possible. The sphere-packing problem can be generalized to any number of dimensions. In two
dimensions, we have circle-packing. In 500 dimensions, we have the packing of 500-dimensional
hyperspheres. The density of a packing is deﬁned as the fraction of the total volume (or area, or
n-dimensional volume) occupied by the spheres. For the purposes of this problem, packings will
always tessellate n-dimensional space, so their density can be calculated by analyzing one tessella.
If the centers of the spheres of a packing form a lattice, we say that a basis for this lattice is
also a basis for the packing. For simplicity, we will consider only packings of n-dimensional space
extending inﬁnitely in all directions, not of containers with boundaries.
a) Draw a diagram of the densest (2-dimensional) circle packing. No justiﬁcation is necessary.
If we place the center of one circle at the origin, the centers of the circles in the packing from
part (a) form a lattice which we call A2. We will give the name A2 to any lattice having this shape
(so the lattice is only unique up to rotation and scale about the origin).
b) Find a basis for your packing from part (a) if your circles have radius 1
2 and lie in the xy-
plane.
c) If the circles from part (a) have radius
√
2
2 and are placed on the plane x + y + z = 0 in R3, prove
that (1,−1, 0) and (0 , 1,−1) form a basis for the packing, up to rotation.
d) Find the density of the packing in parts (b) and (c).
e) The densest sphere-packing in three dimensions is believed (but not proven) to be one represented
by the lattice D3. Compute the maximum density of this packing.
4 Sub-Lattices of E8
Two n-dimensional vectors (v1, v2, . . . , vn) and (u1, u2, . . . , un) are perpendicular if
n∑
i=1
viui = 0.
For example, the 5-dimensional vectors (1, 4,−3, 2, 8) and (−1, 1, 3,−5, 2) are perpendicular because
1· (−1) + 4· 1 + (−3)· 3 + 2· (−5) + 8· 2 = 0.
a) Given a vector v∈ E8, the set of vectors in E8 that are perpendicular to v form the lattice
3
E7. Taking v = (1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2), describe the resulting lattice E7, giving necessary and suf-
ﬁcient conditions for a point to be in the lattice, as well as the minimal norm and the number of
minimal vectors.
Any n-dimensional lattice Ln has a dual lattice Ln∗ consisting of all n-dimensional vectors
(x1, x2, . . . , xn) such that
n∑
i=1
xiui is an integer for every vector ( u1, u2, . . . , un)∈ Ln.
b) One of the minimal vectors in E7∗ is ( 1
4 , 1
4 , 1
4 , 1
4 , 1
4 , 1
4 ,−3
4 ,−3
4). How many minimal vectors
are there in E7∗?
Given a subset Λ of E8 that forms a (rotated) lattice A2, all the vectors in E8 that are perpen-
dicular to every vector in Λ form the lattice E6.
c) Prove that (1 , 0, 0, 0, 0, 0, 0, 1) and ( 1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2 , 1
2) form a basis for A2.
d) Using the version of A2 from (c), ﬁnd the minimal vectors of E6.
e) Find the minimal vectors of E6∗.
5 Complex Lattices
A complex lattice is a lattice with complex coordinates instead of real coordinates. A complex
n-dimensional Gaussian lattice Λ has a basis v1, v2, . . . , vn of vectors with complex coordinates, and
any vector in Λ may be expressed in the form
n∑
i=1
kivi, where k1, k2, . . . , kn are Gaussian integers.
The Gaussian integersG are the numbers of the form a + bi, where a and b are integers.
The ordered pair ( x, y) can be used to represent the complex number x + yi, so any 2 n-
dimensional real lattice can be expressed as an n-dimensional complex lattice. For example, the
lattice Z2 is the complex lattice G1.
a) Express the real lattice Z2m as an m-dimensional complex lattice over the Gaussian integers.
Another sort of complex lattice can be deﬁned over the Eisenstein integers E (instead of the
Gaussian integers), the set of numbers of the form a + bω, where a and b are real integers and
ω = −1+
√
3i
2 . (Note that ω3 = 1.) The Eisenstein integers are useful for expressing hexagonal and
4
diamond lattices as complex lattices. For example, the lattice A2 can be simply expressed as the
complex latticeE 1.
b) Consider the complex 3-dimensional Eisenstein lattice with basis vectors (
√
3i, 0, 0), (1,−1, 0),
and (1, 0,−1). Find the minimal vectors of this lattice, and show that the lattice is equivalent to
E6∗ (ie., that it has the same properties as the lattice found in part (e) of question 4).
5
