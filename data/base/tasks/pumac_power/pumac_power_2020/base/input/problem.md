# PUMaC Power Round 2020

PUMaC 2020* Power Round
Spring 2021
Rules and Reminders
1. Your solutions should be turned in by 12PM Thursday, March 25th, EDT. You
will submit the solutions through Gradescope. The instructions describing how to log
into Gradescope will be sent to the coaches. The deadline for submission is clearly
visible on the Gradescope site once you enroll in the course.
Please make sure you submit you work in time. No late submissions will be
accepted. Please do not submit your work using email or in any other way. If you
have questions about Gradescope, please post them on Piazza.
You may either typeset the solutions in L ATEX or write them by hand. We strongly
encourage you to typeset the solutions. This way, the proofs end up being more clear
and the chances are you will not lose points there. Moreover, you might want to use
some of the LATEX resources listen in point 2.
In case your solutions are handwritten, the cover sheet (the last page of this document)
should be the ﬁrst page of your submission. In case you typeset your solutions, please
take a look at the Solutions Template we posted and make sure to make the cover
sheet the ﬁrst page of your submission.
Each page should have on it the team number (not team name) and problem
number. This number can be found by logging in to the coach portal and selecting
the corresponding team. Solutions to problems may span multiple pages, but include
them in continuing order of proof.
2. You are encouraged, but not required, to use L ATEX to write your solutions. If you
submit your power round electronically,may submit several times, but only your
ﬁnal submission will be graded (moreover, you may not submit any work after
the deadline). The last version of the power round solutions that we receive from your
team will be graded. Moreover, you must submit a PDF . No other ﬁle type will
be graded.
3. Do not include identifying information aside from your team number in your solutions.
4. Please collate the solutions in order in your submission. Each problem should start
on a new page (there is a point deduction for not following this formatting).
5. On any problem, you may use without proof any result that is stated earlier in the
test, as well as any problem from earlier in the test, even if it is a problem that your
team has not solved. These are the only results you may use. In particular, to solve a
problem, you may not cite the subsequent ones. You may not cite parts of your proof
of other problems: if you wish to use a lemma in multiple problems, please reproduce
it in each one.
6. When a problem asks you to “ﬁnd”, “ﬁnd with proof,” “show,” “prove,” “demon-
strate,” or “ascertain” a result, a formal proof is expected, in which you justify each
step you take, either by using a method from earlier or by proving that everything you
do is correct. When a problem instead uses the word “explain,” an informal expla-
nation suﬃces. When a problem instead uses the word “sketch” or “draw” a clearly
marked diagram is expected.
7. All problems are numbered as “Problem x.y” where x is the section number and y is
the the number of the problem within this section. Each problem’s point distribution
can be found in the cover sheet.
8. You may NOT use any references, such as books or electronic resources,
unless otherwise speciﬁed. You may NOT use computer programs, calcu-
lators, or any other computational aids.
9. Teams whose members use English as a foreign language may use dictionaries for
reference.
10. Communication with humans outside your team of 8 students about the
content of these problems is prohibited.
11. There are two places where you may ask questions about the test. The ﬁrst is Piazza.
Please ask your coach for instructions to access our Piazza forum. On Piazza, you may
ask any question so long as it does not give away any part of your solution
to any problem. If you ask a question on Piazza, all other teams will be able to see
it. If such a question reveals all or part of your solution to a power round question,
your team’s power round score will be penalized severely. For any questions you
have that might reveal part of your solution, or if you are not sure if your question
is appropriate for Piazza, please email us at pumacpowerround2020@gmail.com. We
will email coaches with important clariﬁcations that are posted on Piazza.
Introduction and Advice
This year’s power round is about polyhedra. We will study various kinds of lines
and segments on poolyhedra, combining their geometric and combinatorial properties. The
questions will be motivated by extremal situations, such as making some paths as short as
possible.
The power round is structured such that it will walk you through proofs of some of the
important theorems, by giving you hints and problems along the way.
Here is some further advice with regard to the Power Round:
• Read the text of every problem! Many important ideas are included in problems
and may be referenced later on. In addition, some of the theorems you are asked to
prove are useful or even necessary for later problems.
• Make sure you understand the deﬁnitions . A lot of the deﬁnitions are not easy
to grasp; don’t worry if it takes you a while to fully understand them. If you don’t,
then you will not be able to do the problems. Feel free to ask clarifying questions
about the deﬁnitions on Piazza (or email us).
• Don’t make stuﬀ up: on problems that ask for proofs, you will receive more points
if you demonstrate legitimate and correct intuition than if you fabricate something
that looks rigorous just for the sake of having “rigor.”
• Check Piazza often! Clariﬁcations will be posted there, and if you have a question
it is possible that it has already been asked and answered in a Piazza thread (and
if not, you can ask it, assuming it does not reveal any part of your solution to a
question). If in doubt about whether a question is appropriate for Piazza,
please email us at pumacpowerround2020@gmail.com.
• Don’t cheat: as stated in Rules and Reminders, you may NOT use any references
such as books or electronic resources. If you do cheat, you will be disqualiﬁed and
banned from PUMaC, your school may be disqualiﬁed, and relevant external institu-
tions may be notiﬁed of any misconduct.
Good luck, and have fun!
– Daniel Carter, Igor Medvedev, Aleksa Milojevic, Alan Yan
We would like to acknowledge and thank many individuals and organizations for their
support; without their help, this Power Round (and the entire competition) could not exist.
Please refer to the solutions of the power round for full acknowledgments and references.
Contents
1 Playing Billiard 6
2 Introduction to ant-paths 8
3 More about polyhedra 11
4 Ant-paths on tetrahedra 13
5 Ant-paths on cubes 15
Notation
•∀: for all. Ex.:∀x∈{ 1, 2, 3} means “for all x in the set {1, 2, 3}”
• A⊂B: proper subset. Ex.:{1, 2}⊂{ 1, 2, 3}, but {1, 2}̸⊂{ 1, 2}
• A⊆B: subset, possibly improper. ex.:{1},{1, 2}⊆{ 1, 2}
• f :x↦→y: f maps x to y. Ex.: if f(n) = n− 3 then f : 20↦→ 17 and f :n↦→n− 3
are both true.
•{x∈ S : C(x)}: the set of all x in the set S satisfying the condition C(x). Ex.:
{n∈ N :√n∈ N} is the set of perfect squares.
• N: the natural numbers, {1, 2, 3,... }.
• [n] ={1, 2, 3,...,n}.
• Z: the integers.
• R: the real numbers.
•|S|: the cardinality of set S.
1 Playing Billiard
Alex loves playing billiard. Recently, he learned that the billiard balls bounce oﬀ the walls
of the billiard table at the same angles they come in. Further, when a ball hits a corner of
the table it may chose to bounce oﬀ any line between the two lines incident to that corner.
Alex is a good geometer and has precisely deﬁned this billiard game on an arbitrary convex
polygon.
Deﬁnition 1.A. A broken lineA1A2...A n is a union of line segmentsA1A2,A 2A3,...A n−1An.
We sat a broken line is closed if A1 = An and we call A1,...,A n the breakpoints of this
broken line.
Deﬁnition 1.B. Let P be a convex polygon. A broken line A1A2...An is called a billiard
trajectory on P if:
• The points Ai lie on the boundary of P , for i = 1,...,n .
• If Ai lies in the interior of the edge XY of P , we have ∠Ai−1AiX = ∠YA iAi+1.
• If Ai is a vertex of P , adjacent to the vertices X and Y of P , then
|∠XA iAi−1− ∠Ai+1AiY| + ∠XA iY ≤ 180°
Now, Alex is interested what kinds of trajectories he can ﬁnd on a polygon, and has one
more deﬁnition.
Deﬁnition 1.C. LetA1A2...An+1 be a billiard trajectory on a polygon P . If A1 =An and
A2 =An+1, then A1...An is called a closed trajectory. For a closed trajectory C consisting
of n line segments, we deﬁne its order as |C| =n.
Clearly, if there is at least one closed trajectory C on a polygon P , there is inﬁnitely
many of them, obtained by walking several times overC. Trajectories obtained by repeating
several times the same basic closed trajectory C are called powers of C. Trajectories that
cannot be obtained as powers are called prime.
Theorem 1.I. For any convex polygon P there exist inﬁnitely many prime closed billiard
trajectories on P .
We will prove this theorem in several steps. The main idea is to take a longest closed
broken line L with vertices on the boundary of P and at most n vertices, for some wisely
chosenn.1 The following three problems will show that this line satisﬁes the conditions of
the theorem 1.I.
Problem 1.1. Prove that L has exactly n vertices.
Problem 1.2. Prove that L is indeed a closed billiard trajectory, in the sense of deﬁni-
tions 1.B and 1.C.
1Although it may not be utterly obvious that such a maximal broken line exists, this follows by a simple
compactness argument. However, as this is not our topic here, you may assume without proof that such a
maximal broken line exists.
Problem 1.3. Complete the proof of theorem 1.I.
A similar idea can be applied to prove another result of the same ﬂavor.
Problem 1.4. Prove that, given any two pointsA,B on the boundary of a convex polygon
P , there exists inﬁnitely many billiard trajectories starting at A and ending at B.
2 Introduction to ant-paths
Alan the Ant lives on the surface of a three-dimensional polyhedron P. His life consists of
moving along this surface, in a speciﬁc manner. Every day, Alan chooses two points X and
Y on that surface, positions himself at X and tries to get as fast as possible to Y . To do
that, he needs to ﬁnd a shortest path between X and Y on the surface of P.
To formalize these concepts, we have the following deﬁnitions. Although these deﬁnition
may seem cumbersome at ﬁrst, they are only rephrasing the intuition we have about poly-
hedra and their surfaces in mathematical terms. The ﬁrst deﬁnition gives us the concept of
the polyhedron:
Deﬁnition 2.A. A half-space is a region on one side of the plane. Half-spaces can be closed
or open, depending on whether they contain the bounding plane or not. A set of points
in R3 is said to be bounded if there is a big enough ball containing it. A polyhedron is a
bounded intersection of several closed half-spaces.
The following deﬁnition will formalize the concept of the surface of that polyhedron.
Deﬁnition 2.B. Let P be a polyhedron and let H be a plane which does not intersect the
interior of P. If the intersection of H and P is a point, that point is called a vertex of P. If
H∩ P is a line segment, that line segment is called an edge of P, while if H∩ P is a plane
polygon, it is called a face of P. The set of vertices of P is denoted by V (P). The surface
of P is the union of all its faces. We denote the surface of P byS(P).
Finally, the last deﬁnition explains what a path on the surface is and how we measure
its length.
Deﬁnition 2.C. Let X and Y be two points on the surface of a polyhedron P. A path
between X and Y on the surface S(P) is a continuous curve C⊂ S(P), having one end
in X and the other end in Y . For any such curve C, we can pick several points along
it, say X = T0,T 1,T 2,...,T k = Y in that order along C, such that the segments of C
between Ti and Ti+1 lie on only one face. Then, as the segments Ti and Ti+1, we can
measure their length and denote it by l(TiTi+1). Now, we can deﬁne the length of C as
l(C) = l(T0T1) +l(T1T2) +··· +l(Tk−1Tk). A shortest path between X and Y is the path
betweenX and Y with the minimum length.
It turns out that shortest paths on a surface of a polyhedron are exceedingly interesting,
as the following properties show:
Problem 2.1. Let C be the shortest path between points X and Y on the surface of
polyhedron P. Prove that the interior of C does not contain any vertices of P. In other
words,C contains no vertices of P except maybe X and Y .
Hint: Argue by contradiction. Assume there is a shortest path C between X and Y
going through the vertex V and use it to construct a path from X to Y shorter than C to
get a contradiction.
Problem 2.2. Let C be the shortest path between points X and Y on the surface of
polyhedron P. Given an edge AB of P, show that C intersectsAB only in isolated points.
In other words, show that C does not contain a subsegment of AB of nonzero length.
Moreover, show that whenever C intersects AB, it changes the face (i.e. C uses the edge
AB only when it goes from one face to the other).
Hint: Argue by contradiction, as before. Assume that some forbidden structure exists,
and use it to construct a shorter path.
Problem 2.3. Let C be the shortest path between points X and Y on the surface of
polyhedron P. Given an edge AB of P we pick a subsegment KL of C which intersects
AB at exactly one point, T . Show that ∠KTA = ∠BTL (the angles are measured in their
respective planes).
The above nice properties motivate the following deﬁnition, which generalizes the con-
cept of shortest paths, while maintaining all its useful properties.
Deﬁnition 2.D. Let P be a polyhedron and S(P) its surface. An ant-path on S(P) is a
piecewise linear curveC which satisﬁes the following: for every pointP in the interior, there
is a subsegment XPYP of C which contains P , and on which C agrees with the shortest
path between XP and YP .
In other words, an ant-path is a path which looks like a shortest path when zoomed in
enough. As we shall see in the next problem, the properties that we proved for the shortest
paths above are enough to guarantee something is an ant path.
Problem 2.4. Let C be a piecewise linear curve on the surface S(P) of the polyhedron,
with breaking points T1,T 2,...,T k. Prove that C is an ant-path if and only if it satisﬁes the
following three properties:
• All of the breaking points T1,T 2,...,T k lie on the edges of P,
• C contains no vertices in its interior,
• If the breaking point Ti is contained in a short subsegment KL (K and L being on
the diﬀerent faces of P) of C, and on the edge AB of P, then ∠KTiA = ∠BTiL.
Remark: Formally, to solve this problem you need to prove two directions. However,
you will ﬁnd one of them easy due to the work we already did.
Of special interest are ant-paths that do not have beginnings or ends: the closed ant-
paths.
Deﬁnition 2.E. A closed ant-path is a ant-path C whose beginning and end coincide. If
this point is denoted by P , C needs to satisfy: there is a subsegment XPYP of C which
contains P , and on which C agrees with the shortest path between XP and YP . A closed
ant-path is simple if it has no self-intersections.
Interestingly enough, the simple closed ant-paths are relatively rare. The following
problem shows that generic tetrahedrons almost never contains simple closed ant-paths.
Problem 2.5. Let A1A2A3A4 be a tetrahedron, and let θi denote the sums of angles at
the vertex Ai (in other words, θ1 = ∠A2A1A3 + ∠A2A1A4 + ∠A4A1A3, and similarly for
the other indices). If θi +θj̸= 2π for all i̸=j∈ [4], then there is no simple closed ant-path
with 3 or 4 segments on S(A1A2A3A4).
Hint: Try to draw such a path and show it cannot exist due to angle constraints given
by the problem 2.4.
The above result can be generalized to many other polyhedra. In some sense, almost
no generic polyhedra have simple closed ant paths on their surfaces. However, in order to
prove that, we will need to develop a stronger machinery.
3 More about polyhedra
We will now recall some of the well-known properties of the polyhedrons, and also introduce
some on the new ones. One of the most famous results describing 3-dimensional polyhedra
is the celebrated Euler’s formula:
Problem 3.1. Let P be a polyhedron havingV vertices,E edges andF faces. The following
formula relates these three quantities: V−E +F = 2.
Hint: Form a planar graph out of this polyhedron and sum up its angles.
As we aim to generalize the result of problem 2.5, we will follow a similar path, and thus
deﬁne the following quantity:
Deﬁnition 3.A. For a vertex v of the polyhedron P, we deﬁne its pointiness as p(v) =
2π− ∑
iαi, where αi are the face angles of P at the vertex v.
Although the following deﬁnition may seem slightly arbitrary at ﬁrst, the following claim
shows that it is actually useful:
Problem 3.2. For a polyhedron P, we have ∑
v∈V (P)p(v) = 4π.
The preceding problem reminds us of two dimensional case, which we can perhaps solve
ﬁrst in order to build intuition.
Problem 3.3. Let M be a plane polygon, with vertices X1,...,X k. For every vertex Xi,
we can deﬁne the outside angle at Xi as π minus the angle of M at Xi. Then, the sum of
outside angles is 2π.
After having learned how pointiness of vertices behave, we can link that behaviour with
ant-paths.
Problem 3.4. LetC be a simple closed ant-path on the surface of P. It divides the surface
S(P), and the vertices of V (P) consequently, into two parts. The sum of pointiness of
vertices in each part is equal to 2 π.
The previous problem now gives an even simpler solution to problem 2.5. As there is no
way to ﬁnd two vertices with pointiness adding up to 2π (by the constraints of the problem),
there are no simple closed ant-paths on the surface of the tetrahedron. Furthermore, the
previous claim gives us a very strong tool when showing that a given polyhedron has no
simple closed ant-paths - it is enough to check that no subset of its vertices has the sum of
pointiness equal to 2π. In some sense, this means that the most of polyhedra do not have
simple closed ant-paths on their surfaces (making these concepts more precise would be out
of scope of this power round).
The inverse of the previous theorem does not hold, as we will show in the following
problem.
Problem 3.5. Explicitly construct a polyhedron P with no simple closed ant-paths such
that there is a set of its vertices V0⊂V (P) in which ∑
v∈V0p(v) = 2π.
There is one more, somewhat surprising result, concerning diﬀerent ant-paths on poly-
hedrons:
Problem 3.6. Let P be a polyhedron with two diﬀerent simple closed ant-paths C1 and
C2 which do not intersect. Then, these ant-paths have the same length.
4 Ant-paths on tetrahedra
In this section we will examine the simple closed ant-paths on the surfaces of various tetra-
hedra. We start oﬀ by examining and classifying the ant-paths on the regular tetrahedron.
We are interested in a question of the form: what are all of the possible lengths of
ant-paths on the surface of the regular tetrahedron. First, we will notice that a tetrahedron
has a very special property that makes it even simpler than other regular polyhedra.
Problem 4.1. Let ABCD be a regular tetrahedron, assume the face ABC is horizontal,
and denote this plane by α. Prove that it is possible to roll the given tetrahedron on this
plane such that the faces of the tetrahedron form a triangular tiling of the plane. Moreover,
prove that it is possible to assign letters a,b,c,d to the vertices of this tiling such that
the vertex A of the tetrahedron always lands on the vertex of the tiling marked by a, and
similarly for the vertices B,C,D .
Having constructed this useful rolling of the tetrahedron on the plane, we can start
dealing with ant-paths. Assume theS(ABCD ) contains an ant-pathC. Roll the tetrahedron
ABCD along this ant-path, until we come back where we started on the ant-path. In the
plane, this ant-path will have the following form: its endpoints will be on the edges of the
tiling marked by the same letters, and oriented the same way (e.g. both endpoints will be
on the edges ab of the tiling, and a is left of b on both edges). Moreover, as long as such
a plane segment does not contain any vertices of the tiling, it will be possible to uniquely
bring it back on the surface of ABCD .
Problem 4.2. Prove that all closed ant-paths on the surface of ABCD are simple. (You
may assume that the ant-paths do not repeat themselves several times.)
Hint: How are the cells of the tiling corresponding to the same face oriented?
Now, we are able to produce an answer to our starting question:
Problem 4.3. Assume tetrahedron ABCD has unit edge length. Find all possible lengths
of closed ant-paths.
Now, having solved the main question in case of regular tetrahedron, we will broaden
our focus. There is one speciﬁc family of tetrahedra, called equihedral tetrahedra which
behave very nicely with respect to ant-paths. These tetrahedrons are deﬁned as follows:
Deﬁnition 4.A. A tetrahedron ABCD is called equihedral if its four faces ABC, ADC,
ADB, and CDB are all congruent.
A useful way to visualize equihedral tetrahedra is as the face diagonals of a rectangular
prism:
Problem 4.4. Prove that ifABCD is an equihedral tetrahedron, there exists a rectangular
prism where four of its eight vertices are A, B, C, and D, and the six edges of ABCD are
diagonals of the six faces of the prism.
There are many other statements which are equivalent to the given deﬁntion of a tetra-
hedron being equihedral:
Problem 4.5. Let ∆ be a tetrahedron with vertices ABCD . Prove that the following
statements are equivalent:
• ∆ is equihedral in the sense of Deﬁnition 4.A.
• The perimeters of all faces ABC, ABD, ACD, and BCD are equal.
• The pointiness of all vertices are equal, i.e. p(A) =p(B) =p(C) =p(D).
• The dihedral angles at the opposite edges are equal. In other words, the angle between
planesABC andBCD is equal to the angle between the planes ACD andABD (and
similarly for other pairs of planes).
• The solid angles at each vertex have the same measure.
Remark: The solid angle at the vertex V of a tetrahedron can be deﬁned as follows: if
S is a sphere of radius r aroundV ,r being small enough that this sphere does not intersect
other edges of the tetrahedron except the ones incident to V , then the solid angle at V is
the ratio of the area of S contained in V to the square of the radius.
Equihedral tetrahedra turn out to be exceedingly interesting when discussing ant-paths.
The following problems show us several examples of this correlation.
Problem 4.6. Prove that there are three pairwise intersecting simple closed ant-paths on
a tetrahedron if the tetrahedron is equihedral.
Problem 4.7. Two closed ant-paths on the surface of the tetrahedron are called similar if
they intersect the edges of the tetrahedron in the exact same order. Prove that a tetrahedron
has inﬁnitely many non-similar closed ant-paths if and only if it is equihedral.
5 Ant-paths on cubes
Having thoroughly examined the case of both regular and equihedral tetrahedra, we turn
to the case of the cube. More precisely, we are interested in which are the possible lengths
of ant-paths on the surface of a cube. Unfortunately, when dealing with the cube, there
is no statement analogous to problem 4.1. Therefore, when extending the claims about
tetrahedra to cubes, we need to have a diﬀerent approach when unrolling a cube onto the
plane.
Problem 5.1. Let ABCDA′B′C′D′ be a cube and let α be the plane supporting the side
ABCD . Rolling the cube over its edges onto α will give the integer-point lattice in the
plane. Prove that it is not possible to label the vertices of this lattice by a,b,c,d,a ′,b′,c′,d′
so that the vertex A of the cube always lands at the point label a, vertex B at b, etc.
The last problem means that we will have to label the vertices on the plane depending
on the ant-path we are examining at the moment. More precisely, to each closed ant-path,
we will associate a straight planar segment of the same length. Then, we will examine
which planar segments can be obtained from ant-paths, which will lead us towards a better
understanding of ant-paths on the surface of the cube and of their lengths.
To construct a straight planar segment, we assume we have an ant-pathC that intersects
the edge AB and goes into the face ABCD afterwards. Moreover, assume X∈ C∩AB
and XA =d. For the sake of simplicity we place the face ABCD onto the unit square on
the plane, and let X have coordinates (d, 0). Then, we unroll the cube along C. At some
point, after the whole ant-path is unrolled, the point X will come back on the plane, thus
marking the point X′.
Problem 5.2. Prove that the point X′ will have the coordinates of the form ( d +m,n ),
for some positive integers m∈ Z,n∈ Z>0. Further, prove that the length of the planar line
segmentXX′ is equal to the length of C. Here, you may assume C is simple if that helps.
However, not every segment going from (d, 0) to (d +m,n ) corresponds to an ant-path.
Problem 5.3. Give an example showing the previous claim (i.e. ﬁnd some d,m,n such
that the segment from (d, 0) to (d +m,n ) cannot be produced from the ant-path using the
above procedure).
Therefore, our goal is to ﬁnd which segments from X = (d, 0) to X′ = (d +m,n )
correspond to actual closed ant-paths on the cube. There is one easy way to determine this
for anyd,m,n . Start by labeling the vertices of the unit square by a,b,c,d and by unrolling
the cube over the segmentXX′. When a vertex V of the cube falls onto the plane, label the
point by v (V ∈{ A,B,C,D,A ′,B′,C′,D′}). If X′ ends up on the horizontal edge whose
left label is a and whose right label is b (the left label corresponding to the point ( m,n ),
and the right on to the point ( m + 1,n )), then the cube have made a full rotation and we
have an ant-path.
Note that the segment XX′ contains no points with integer coordinates. From now on,
whenever we consider segments of this type, we will exclude the segments containing the
integer points.
In general, given some ﬁxed m,n , and d∈ [0, 1], the labels of the points ( m,n ) and
(m + 1,n ) could depend on d. However, we have the following claim that eliminates this
possibility in case the points ( m,n ) and (m + 1,n ) were labeled a and b, as the following
problem suggests.
Problem 5.4. If for given m,n∈ Z+, the points (m,n ) and (m + 1,n ) get labels a,b for
some d under the described procedure, they get the same labels for all but ﬁnitely many
d∈ [0, 1].
The last problem tells us the fact whether the triple (m,n,d ) corresponds to an ant-path
does not really depend on d - if (m,n,d ) comes from an ant-path for one value of d, it does
so for almost any other value of d. Thus, one can deﬁne the pair ( m,n ) to be good if there
is some d such that (m,n,d ) corresponds to an ant-path. Moreover, as we have it is easy to
see that m andn are enough to determine the length of the ant-path C, because the length
of the segment XX′ is XX′ =
√
m2 +n2.
This property helps us determine the lengths of all the ant-paths on a cube. However,
before doing that, we will classify the simple - non-intersecting ant paths on a cube. To
this end, we have two lemmas that provide a great reduction in terms of various m and n
we have to consider.
Problem 5.5. Let C be a closed ant-path on the surface of the cube which has a self-
intersection at a point A. Prove that the ant-path is perpendicular to itself at A.
Problem 5.6. Let C be a closed ant-path on the surface of the cube which has an unfolding
on the plane from ( d, 0) to (m +d,n ). Prove that if m +n≥ 7, the ant-path has a self-
intersection.
Using the last problem, we can determine the lengths of all non-intersecting ant-paths
on a cube.
Problem 5.7. Find the lengths of all non self-intersecting closed ant-paths on the surface
of a cube. For each length you ﬁnd, sketch an ant-path of that length on the surface of the
cube.
Further, we will prove that we can ﬁnd an ant-path corresponding to almost any direction
in the plane.
Problem 5.8. Letm,n be two coprime non-negative integers (not both being zero). Then,
there exists a unique integer k≤ 4 for which the pair (km,kn ) corresponds to an ant-path
(that does not repeat itself).
Hint: If (m,n ) is not a good pair by itself, what are the labels of the points (m,n ) and
(m + 1,n ). Can you make any inference about the labels of (2m, 2n) and (2m, 2n + 1) based
on this?
The statement of the last problem seems incomplete: how to determinek based onm,n ?
The following asks for any progress towards determining whichk corresponds to which pairs
m,n :
Problem 5.9. Prove that k always comes from {2, 3, 4} in the last problem. Determine
which values can k take depending on the parity of m,n .
Hint: Although there is a decisive answer to this question, this problem is intended to
be open ended. Whatever conclusions you might have about how to determine k, make sure
to write them down.
Finally, to outline the usefulness of this approach, we pose a computational question:
Problem 5.10. What are the ﬁve shortest lengths of closed, non-repeating ant-paths on
the surface of the cube?
Team Number:
PUMaC 2020* Power Round Cover Sheet
Remember that this sheet comes ﬁrst in your stapled solutions. You should submit
solutions for the problems in increasing order. Write on one side of the page only. The
start of a solution to a problem should start on a new page. Please mark which questions
for which you submitted a solution to help us keep track of your solutions.
Problem Number Points Attempted?
1.1 10
1.2 20
1.3 20
1.4 15
2.1 20
2.2 20
2.3 20
2.4 20
2.5 30
3.1 10
3.2 20
3.3 5
3.4 35
3.5 25
3.6 30
4.1 10
4.2 20
4.3 30
4.4 20
4.5 60
4.6 50
4.7 50
5.1 10
5.2 20
5.3 10
5.4 40
5.5 20
5.6 30
5.7 30
5.8 30
5.9 60
5.10 20
