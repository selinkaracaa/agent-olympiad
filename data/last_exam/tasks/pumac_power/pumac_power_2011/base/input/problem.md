# PUMaC Power Round 2011

Power Round: Geometry Revisited
Stobaeus (one of Euclid’s students): ”But what shall I get by learning these
things?”
Euclid to his slave: ”Give him three pence, since he must make gain out of what
he learns.”
- Euclid, Elements
1 Rules
These rules supersede any rules appearing elsewhere about the Power Test.
For each problem, you may use without proof any result (problem, lemma, proposition,
exerice, or theorem) occurring earlier in the test, even if it’s a problem your team has not
solved. You may cite results from conjectures or subsequent problems only if your team
solved them independently of the problem in which you wish to cite them. You may not
cite parts of your proof of other problems: if you wish to use a lemma in multiple problems,
reproduce it in each one.
It is not necessary to do the problems in order, although it is a good idea to read all
the problems, so that you know what is permissible to assume when doing each problem.
However, please collate the solutions in order in your solution packet. Each problem should
start on a new page.
Using printed and noninteractive online references, computer programs, calculators, and
Mathematica (or similar programs), is allowed. (If you ﬁnd something online that you think
trivializes part of the problem that wasn’t already trivial, let us know—you won’t lose points
for it.) No communication with humans outside your team about the content of these prob-
lems is allowed.
2 Prerequisites
We open with a quick exercise. When we say that D∈ BC, we mean that D is a point
anywhere in the line passing throughBC (not necessarily just the line segmentBC between
them).
Exercise -9 (3 points). Let ABC be a triangle and let D∈ BC, E∈ AC, F∈ AB,
where the six pointsA,B,C,D,E,F are all distinct. Prove that ifD,E, andF are collinear,
then either none or exactly two of D, E, and F lie in their corresponding line segments
1
BC,AC,AB, respectively.
Menelaus’ theorem (triangle version).
LetABC be a triangle and let A1∈BC,B1∈AC,C1∈AB, with none of A1,B1, and C1
a vertex of ABC. Then A1, B1, C1 are collinear if and only if
A1B
A1C· B1C
B1A· C1A
C1B = 1
and exactly one or all three lie outside the segments BC,CA,AB. (We use the convention
that all segments are unoriented throughout this test.)
Menelaus’s Theorem (quadrilateral one-way version).
LetA1A2A3A4 be a quadrilateral and let d be a line which intersects the sides A1A2,A2A3,
A3A4 and A4A1 at the points M1, M2, M3, and M4, respectively. Then,
M1A1
M1A2
· M2A2
M2A3
· M3A3
M3A4
· M4A4
M4A1
= 1.
Exercise -8 (7 points). Prove the quadrilateral one-way version of Menelaus’s Theorem.
Ceva’s theorem.
LetABC be a triangle and let A1∈BC,B1∈AC,C1∈AB, with none of A1,B1, and C1
a vertex of ABC. Then AA1,BB 1,CC 1 are concurrent if and only if
AC1
C1B· BA1
A1C· CB1
B1A = 1
2
and exactly one or all three lie on the segments BC, CA, AB.
Exercise -7 (a) (1 point). In △ABC, suppose D,E, and F are the midpoints of BC,
CA, and AB, respectively. Prove that AD,BE,CF are concurrent.
(b) (2 points). In△ABC, supposeAD is an angle bisector of ∠BAC, and similarly that
BE,CF are angle bisectors. Prove that AD,BE,CF are concurrent.
Exercise -6. Mass point geometry is a method useful in ﬁnding ratios of certain lengths
in setups involving triangles and cevians. Imagine that X and Y are vertices of a triangle.
We may assign masses µ(X),µ (Y )> 0 to the points X andY . Then, the ”center of mass”
of the points X and Y is the point Z on XY such that µ(X)·XZ = µ(Y )·YZ . The
problem-solving strategy is to choose the weights for the vertices of the triangles so that
the centers of masses of the vertices of the triangle coincide with the important points in
the diagram, such as endpoints of cevians. When the masses are chosen this way, then the
center of mass of the triangle is the intersection of the cevians. For more details, examples,
and rigorous deﬁnitions, one can refer to Wikipedia.
(a) (2 points). In△ABC,D is inBC,E is inCA, andF is inAB such thatAD,BE,CF
concur at the point X, and AF = 2,FB = 3,BD = 1,DC = 5. Find AE/CE using mass
points, and without using mass points.
(b) (2 points) Find AD/AX again using mass points, and without using mass points.
(c) (2 points). Find the ratio of the areas of △AFX to△CDX (using any method of
your choice).
Desargues’s theorem. Let ABC andA′B′C′ be two triangles. Let A′′ be the intersection
ofBC andB′C′,B′′ be the intersection of CA andC′A′, and C′′ be the intersection of AB
and A′B′, and assume all three of those intersections exist.
3
Then the lines AA′, BB ′, and CC ′ are concurrent or all parallel if and only if A′′, B′′, and
C′′ are collinear.
Desargues’s Theorem is true even if, for instance, BC and B′C′ are parallel, provided
that one interprets the “intersection” of parallel lines appropriately. We won’t state cases
like the following separately in the future; you may want to google “line at inﬁnity” if you’re
unfamiliar with them.
Exercise -5 (5 points). Let ABC and A′B′C′ be two triangles. Suppose that BC and
B′C′ are parallel, CA andC′A′ are parallel, and AB andA′B′ are parallel. Prove that the
lines AA′, BB ′, and CC ′ are concurrent or all parallel.
Pascal’s theorem. Let A,B,C,D,E,F be six points all lying on the same circle. Then,
the intersections of AB and DE, of BC and EF , and of CD and FA are collinear.
Keep an open mind for degenerate cases, where some of the points are equal! For this
theorem, if two of the points are the same, then the line through them is the tangent to the
circle at that point.
Exercise -4 (5 points). Suppose the incircle of △ABC is tangent to BC,CA,AB at
D,E,F , respectively. Let X,Y,Z be the intersections of AB and DE, BC and EF , CA
and FD , respectively. Show that X,Y,Z are collinear.
In fact, we may replace the circle in Pascal’s Theorem with an arbitrary conic section.
When we consider the degenerate conic section given by two lines, we obtain the statement
of Pappus’s theorem:
Pappus’s theorem. Given three collinear pointsA,B,C and three collinear pointsD,E,F ,
4
then if P is the intersection of BF andCE,Q ofAF andCD, and R ofAE andBD, then
P,Q,R are also collinear.
Also, some projective geometry notions might come in handy at some point. We introduce
below the notions of harmonic division , harmonic pencil , pole, polar, and mention some
lemmas that you may want to be familiar with.
Let A, C, B, and D be four points on a line d. If they are in that order on d, the
quadruplet (ACBD ) is called a harmonic division (or just “harmonic”) if and only if
CA
CB = DA
DB.
Notice that this deﬁnition remains invariant if we swap the orders of A,B and/or C,D on
the line. Thus, if the four points lie in the order A,D,B,C orB,C,A,D orB,D,A,C , we
may deﬁne the harmonic division (ACBD ) in the same way.
Exercise -3 (3 points). Suppose A = (1, 0), B = (5, 4), and C = (4, 3). Find D such
that (ACBD ) is harmonic, E such that (ACEB ) is harmonic, and F such that (AFCB )
is harmonic.
IfX is a point not lying on d, then the “pencil” X(ACBD ) (consisting of the four lines
XA,XB,XC ,XD) is called harmonic if and only if the quadruplet (ACBD ) is harmonic.
So in this case, X(ACBD ) is usually called a harmonic pencil.
Now, the polar of a point P in the plane of a given circle Γ with center O is deﬁned as
the line containing all points Q such that the quadruplet ( PXQY ) is harmonic, where X
andY are the intersection points with Γ of a line passing through P . This polar is actually
a line perpendicular to OP ; when P lies outside the circle, we can see from the following
exercise that it is precisely the line determined by the tangency points of the circle with the
tangents from P . We say that P is the pole of this line with respect to Γ.
5
Exercise -2 (2 points). Let O be the circle of radius 2 centered at the origin, and let
P = (a,a ) for some a̸= 0. Find the polar of P with respect to O.
Given these concepts, there are four important lemmas that summarize the whole the-
ory. Remember them by heart even though you might prefer not to use them in this test.
They are quite beautiful.
Lemma 1 . In a triangle ABC consider three points X, Y , Z on the sides BC, CA,
and AB, respectively. If X ′ is the point of intersection of the line YZ with the extended
sideBC, then the quadruplet (BXCX ′) is a harmonic division if and only if the lines AX,
BY , CZ are concurrent.
Lemma 2 . Let ℓ and ℓ′ be two lines in plane and let P be a point in the same plane
but not lying on either ℓ orℓ′. Let A,B,C,D be points on ℓ and let A′,B′,C′,D′ be the
intersections of the lines PA , PB , PC , PD with ℓ′, respectively. Then
BA
BC : DA
DC = B′A′
B′C′ : D′A′
D′C′.
Conversely, ifA = A′; A,B,C,D and A′,B ′,C ′,D ′ lie in those orders on ℓ and ℓ′, respec-
tively; and the cross-ratio above holds, then the lines BB ′, CC ′, DD′ are concurrent.
Lemma 3 . Let A, B, C, D be four points lying in this order on a line d. If X is a
point not lying on this line, then if two of the following three propositions are true, then
the third is also true:
• The quadruplet (ABCD ) is harmonic.
• XB is the internal angle bisector of ∠AXC .
• XB⊥XD.
Lemma 4 . If P lies on the polar of Q with respect to some circle Γ, then Q lies on the
polar of P .
Exercise -1 (a) (3 points). Prove Lemma 1. (b) (6 points). Prove Lemma 2.
Reminder 0 (0 points). On every page you submit, put your team’s name, a page
count, and solutions to problems from at most one problem.
This is it. You are now ready to proceed the next section. As Erd˝ os would advise you,
keep your brain open!
6
3 The Test
General Setting . We are given a scalene triangle ABC in plane, with incircle Γ, and we
let D, E, F be the tangency points of Γ with the sides BC, CA, and AB, respectively.
Furthermore, let P be an arbitrary point in the interior1 of the triangle ABC and let
A1B1C1 be its cevian triangle (that is, A1, B1, C1 are the intersections of the lines AP ,
BP ,CP with the sidesBC,CA, andAB, respectively); fromA1,B1,C1 draw the tangents
to Γ that are diﬀerent from the triangle’s sides BC,CA,AB, and let their tangency points
with the incircle be X, Y , and Z, respectively. Now, with this picture in front of you, take
a look at the following results! (ahem... and prove them!)
Proposition 1 (a) (6 points). Extend A1X to intersect AC at V . Show that the lines
AA1, BV , and DE are concurrent.
(b) (12 points). Let A2 be the intersection point of AX with the sideline BC. Show
that
A2B
A2C = s−c
s−b· A1B2
A1C2.
[Hint: Menelaus, Menelaus, Menelaus!]
(c) (2 point). Prove that the lines AX, BY , and CZ are concurrent.
1The point P is considered inside ABC just for convenience, so please don’t worry about the word interior
that much; we just want nice, symmetrical drawings!)
7
Proposition 2 (14 points). The lines B1C1, EF , YZ concur at a point, say A0.
Similarly, the lines C1A1, FD , ZX and A1B1, DE, XY concur at points B0 and C0,
respectively. [Hint: Pascal’s theorem might be useful here.]
Proposition 3 (8 points). The points A0,B,C0 are collinear. Similarly, the points A0,
B0, C are collinear, and A, B0, C0 are collinear. [Hint: Recall Lemma 2.]
8
Proposition 4 (14 points). The triangles A0B0C0 andDEF are perspective2 and their
perspector3 lies on the incircle of △ABC.
Proposition 5 (a) (10 points). Let ABC be an arbitrary triangle, and A′, B′, C′ be
three points on BC,CA,AB. Let also A′′,B′′,C′′ be three points on the sides B′C′,C′A′,
A′B′ of triangle A′B′C′. Then consider the following three assertions:
(1) The lines AA′, BB ′, CC ′ concur.
(2) The lines A′A′′, B′B′′, C′C′′ concur.
(3) The lines AA′′, BB ′′, CC ′′ concur.
If any two of these three assertions are valid, then the third one must hold, too. [Hint:
We didn’t put the quadrilateral version of Menelaus in the Prerequisites section for nothing!]
(b) (4 points). The triangles A0B0C0 and ABC are perspective.
Proposition 6 (10 points). The incenter I of ABC is the orthocenter of triangle
A0B0C0. [Hint: Lemma 2 might prove useful here.]
2Two triangles ABC and XY Z are said to be perspective if and only the lines AX, BY , CZ are
concurrent.
3The perspector of two perspective triangles ABC and XY Z is precisely the common point of the lines
AX, BY , CZ .
9
Proposition 7 (14 points). Let R a point on AC and consider S, T the intersections
of RA0, RC0 with AB and BC respectively. Then, B0 lies on ST .
Proposition 8 (14 points). The triangles ABC and TRS are perspective.
Proposition 9 (20 points). The triangles A0B0C0 and TRS are perspective and the
locus of the perspector as R varies along the line AC is a line tangent to the incircle of
triangle ABC. [Hint: This is the capstone problem of the test, and its solution uses many
of the results you’ve encountered throughout the test.]
10
4 Historical Fact/Challenge
When the pointP chosen at the beginning of the test is the incenter, the Nagel point, or the
orthocenter of triangle ABC, the conﬁguration generates a “Feuerbach family” of circles.
More precisely, maintaining the notations from the previous propositions, the circumcircle
of triangle TRS always passes through the Feuerbach point4 of triangle ABC, as R varies
on the line AC. So, do try and have fun with it after ﬁnishing everything. However, you
will not receive any credit for this problem.
4The incircle and the nine-point circle of a triangle ABC are tangent to each other and their tangency
point is called the Feuerbach point of triangle ABC .
11
