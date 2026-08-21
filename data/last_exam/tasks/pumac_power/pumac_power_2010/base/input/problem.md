# PUMaC Power Round 2010

PUMaC 2010 Power Round:
Graph Minors
These rules supersede any rules appearing elsewhere about the Power Test.
For each problem, you may use without proof the results of all previous
problems (that is, problems that appear earlier in the test), even if your team has
not solved these problems. You may cite results from conjectures or subsequent
problems only if your team solved them independently of the problem in which
you wish to cite them. You may not cite parts of your proof of other problems:
if you wish to use a lemma in multiple problems, reproduce it in each one.
It is not necessary to do the problems in order, although it is a good idea
to read all the problems, so that you know what is permissible to assume when
doing each problem. However, please collate the solutions in order in your
solution packet. Each section should start on a new page.
Using printed and noninteractive online references, computer programs, cal-
culators, and Mathematica (or similar programs), is allowed. (If you ﬁnd some-
thing online that you think trivializes part of the problem that wasn’t already
trivial, let us know—you won’t lose points for it.) No communication with
humans outside your team about the content of these problems is allowed.
Each problem is marked with a number of stars. This is both the test-writers’
estimate of its relative diﬃculty and an indication of what sort of answer we
expect:
★ problems need a short (probably one-sentence) explanation. The explanation
should be just detailed enough that we couldn’t explain anything incorrect by
it.
★★ problems need a proof. Partial credit will be given for ideas useful in a correct
proof.
★★★ problems need a proof, and we reserve half their credit for the elegance of
the proof.
★★★★ problems have the same rules as ★★ problems.
★★★★★ problems need an elegant proof. No points are awarded for an inelegant
one.
Note that giving an answer less rigorous than we expect is worth 0 points: for
instance, if a problem asks you to ﬁnd a graph with certain properties, giving the
graph alone is worth nothing unless you also prove that it has those properties.
Each problem also has a maximum possible score listed after its star rating.
The total number of points available is 1,000,100. Power test scores will be
scaled before use in the rest of PUMaC.
1
1 Basic deﬁnitions
Deﬁnition 1.1. A multiset is a set in which repeated elements are allowed.
The order of the elements does not matter, but the multiplicities do.
Deﬁnition 1.2. A graphG is a multisetE(G) of submultisets (“edges”) of size
2 of a set V (G) (“vertices”).
For instance,{{1, 1},{1, 1},{1, 3},{1, 3},{2, 3},{4, 5}} is a nonsimple graph
on 5 vertices 1, 2, 3, 4, and 5.
For ease of use, we often draw pictures of graphs with the vertices as dots
and the edges as line segments connecting them, and say that two vertices are
adjacent if they’re both elements of some edge.
For instance, the following are two pictures of K4:
You can use these pictures to represent graphs wherever they occur, but
keep in mind that a graph is deﬁned by sets of vertices and edges, not by its
drawings.
Two equal edges of a graph are called parallel edges, and an edge with two
equal vertices is called a loop.
Deﬁnition 1.3. The simpliﬁcation of a graph G is the graph H with all loops
removed, and all but one of each set of parallel edges removed. A graph issimple
if it has no loops or parallel edges.
Here are drawings of the most basic graphs that are not simple:
A few special types of graphs deserve mention:
∙ A complete graphKn is the simple graph onn vertices, every pair of which
are adjacent.
2
∙ A complete bipartite graph on m and n vertices Km,n is the simple graph
with m +n vertices, with each of the ﬁrst m vertices adjacent to each of
the last n (for a total of mn edges).
∙ A cycle Cn hasn verticesv1, . . . ,vn, an edge{vi,v i+1} for each 1≤i<n ,
and an edge{v1,v n}. So for all n, Cn has n edges.
∙ A wheel Wn is Cn plus an extra vertex adjacent to all the vertices of Cn
(by one edge).
Deﬁnition 1.4. A graph G is disconnected if and only if its vertices can be
divided into two nonempty sets A and B such that no vertex of A is adjacent
to any vertex of B. Otherwise, G is connected.
Deﬁnition 1.5. A path between two vertices u and v is a sequence of distinct
vertices v0 = u,v 1,...,v k = v such that for every 0 ≤ i < k, vi is adjacent to
vi+1. The length of such a path is k, the number of edges.
Problem 1.1. (★, 2) For which values of n is Cn simple?
Problem 1.2. (★, 1) How many edges does W6 have?
Problem 1.3. (★★, 4) Prove that a graph G is connected if and only if there’s
a path between every pair of distinct vertices.
Deﬁnition 1.6. If G is a graph and A is a subset of its vertices, then the
subgraph of G induced on A, denoted G∣A, is the graph whose vertex set is A
such that for any u,v ∈A, the multiplicity of the edge {u,v} in E(G∣A) is the
same as the multiplicity of {u,v} in E(G).
Deﬁnition 1.7. If G is a graph and v∈ V (G), then G∖v (“G delete v”) is
G∣V (G)∖{v}.
Problem 1.4. (★, 1) What graph do you get by deleting a vertex of Kn?
Problem 1.5. (★, 4) How many distinct graphs can you get by deleting three
vertices of W2010? Note that, say, two copies of K3 aren’t distinct, even if they
came from diﬀerent vertices of a bigger graph.
Deﬁnition 1.8. IfG is a graph and e∈E(G), then G∖e (“G deletee”) is the
graph with the same vertices as G, and the same multiset of edges except we
remove one copy of e.
Deﬁnition 1.9. A graph H is a subgraph of a graph G if you can get from G
to H by deleting vertices (i.e., taking an induced subgraph) and then deleting
edges.
Problem 1.6. (★, 1) Prove that if a graph G with n≥ 0 vertices doesn’t have
K1 as a subgraph, then it has at most −n edges.
3
2 Edge contraction
Deﬁnition 2.1. If G is a graph and e ={u,v}∈ V (G) (with u and v not
necessarily distinct), then G/e (”G contract e”) is the subgraph of G induced
on all its vertices but u and v, plus an extra vertex , and some new edges
containing : each edge of G of the form {u,a} or{v,a}, for a∕∈ {u,v} is
replaced with an edge {,a}. Each edge of G of the form {u,v},{u,u}, or
{v,v}, is replaced with a loop at , except for e itself.
To picture this, you can imagine that the vertices are big blobs of clay and
each edge is a thin cable connecting two blobs. When you contract an edge,
you mold the cable and the two blobs it connected into one new blob, without
destroying the other cables. For example, if you contract an edge of K5, you
get K3 plus one other vertex sharing two edges with each vertex in K3. If you
contract an edge of K3,3 you get W4.
Problem 2.1. (★, 2)
∙ True or false: You can contract an edge of W4 to get W3.
∙ True or false: If an edge e is a loop (that is, it’s {v,v} for some vertex v),
then G/e =G∖e.
Deﬁnition 2.2. A graph H is a minor of a graph G if and only if you can
“reach H from G by repeatedly deleting a vertex, deleting an edge, or con-
tracting an edge.” That is, if and only if there’s a sequence of graphs G0 =
H,G 1,G 2,...,G k−1,G k = G such that for each i such that 0 ≤ i < k, either
Gi =Gi+1∖v for some vertexv, orGi =Gi+1∖e for some edgee, orGi =Gi+1/e
for some edge e.
Problem 2.2. (★★, 6) Prove that H is a minor of G if and only if you can map
each vertex v∈V (H) to a nonempty subset of G’s vertices f(v)⊂V (G) such
that:
∙ For allv∈V (H), the subgraph of G induced on f(v) is connected.
∙ For allu,v∈V (H) with u∕=v, f(u)∩f(v) ={}.
∙ For allu,v∈V (H),∣E(f(u),f (v))∣−∣f(u)∩f(v)∣≥ E({u},{v})−∣{u}∩
{v}∣, where E(X,Y ) is the number of edges with one endpoint in X and
the other in Y .
Problem 2.3. (★, 3)
∙ Is K5 a minor of K8?
∙ Is K5 a minor of K2,2?
∙ Is K5 a minor of K3,3?
∙ Is K5 a minor of K4,4?
4
∙ Is K5 a minor of K5,5?
∙ Is K5 a minor of C125?
∙ Is K4 a minor of W3?
∙ Is K4 a minor of W5?
∙ Is K5 a minor of W6?
Problem 2.4. (★, 2 points)
∙ What is the smallest n such that K2010 is a minor of Kn,n?
∙ What is the smallest n such that W2010 is a minor of Kn,n?
Problem 2.5. (★, 1) Prove that if a simple graph G withn≥ 1 vertices has no
K2 minor, then it has at most 0 edges.
3 Graph colorings
Deﬁnition 3.1. A graph is k-colorable if and only if you can partition its
vertices into k (possibly empty) subsets such that no vertices within a subset
are adjacent. (Intuitively, the subsets are colors, and no two vertices of the same
color are adjacent.)
Problem 3.1. (★, 1) Find a graph that’s not 3-colorable.
Hadwiger’s conjecture states that if G is a simple graph with no Kt minor,
then G is (t− 1)-colorable.
Problem 3.2. (★★, 4) Prove Hadwiger’s conjecture for t = 3.
Problem 3.3. (★, 2) For eachn≥ 2, ﬁnd a graph G withn vertices, more than
n− 1 edges, and no K3 minor.
4 Planar graphs
Deﬁnition 4.1. A graph is planar if and only if it can be drawn in the plane
with no two edges intersecting. (Edges needn’t be straight lines, although it
happens that every simple planar graph can be drawn with straight-line edges
and no edges intersecting.)
Problem 4.1. (★, 3) Which of the following graphs are planar?
∙ K4
∙ C4
∙ W4
5
∙ K4,4
∙
Problem 4.2. (★★★★★ , 1,000,000) Prove that every loopless planar graph is
4-colorable. (This is called the Four-color theorem).
Problem 4.3. (★★, 4) Prove that if a simple graph G with n≥ 3 vertices has
no K4 minor, then it has at most 2 n− 3 edges.
5 Excluded Minor Theorems
Problem 5.1. (★★, 4) Prove that K5 and K3,3 are not planar.
Problem 5.2. (★★, 2) Prove that if G has a K5 or K3,3 minor, then G isn’t
planar.
A famous theorem of Wagner’s (sometimes attributed to Kuratowski, al-
though he actually proved something else) states that a graph is planar if and
only if it has no K5 minor and no K3,3 minor. The other direction of the proof
is easily googleable, if you’re curious.
Many classic types of graphs can be described easily in terms of minors that
they don’t have. For instance:
∙ Graphs that don’t have C1 (that is, the one-vertex, one-edge graph) as a
minor are forests.
∙ Graphs that don’t have C2 as a minor are forests with loops allowed.
∙ Graphs that don’t have C3 as a minor are forests with loops and parallel
edges allowed.
∙ Graphs that don’t have a path of length 2 as a minor are matchings (plus
isolated vertices, loops, and parallel edges).
Problem 5.3. (★★, 4) What graphs don’t have a path of length 3 as a minor?
Deﬁnition 5.1. A k-sum of two simple graphs G and H takes a Kk subgraph
of each one, identiﬁes the vertices in them (that is, glues the Kks together), and
deletes the edges of the Kk. For instance, a 3-sum of two K4s is K2,3.
6
Problem 5.4. (★, 2) How many distinct graphs can you get as 2-sum of K2,3
and W4?
Problem 5.5. (★★, 4) Prove that if simpleG andH don’t haveK3,3 as a minor,
then no 0-sum, 1-sum, or 2-sum of G and H has K3,3 as a minor.
Problem 5.6. (★★, 2) Is the same true for 3-sums?
Problem 5.7. (★★★ , 8) Prove that if a simple graph G withn≥ 4 vertices has
no K5 minor, then it has at most 3 n− 6 edges.
6 Reminder
Problem 6.1. (, 1) On every page you submit, put your team’s name, a page
count, and solutions to problems from at most one section.
Problem 6.2. (★★★★ , 16) Prove that if a simple graph G with n≥ 5 vertices
has no K6 minor, then it has at most 4 n− 10 edges.
7 The End.
Problem 7.1. (★★, 4) For each n≥ 6, construct a simple graph G with n
vertices, at least 5n− 15 edges, and no K7 minor.
8 Credits
Problem 8.1. (★★★ , 12) For somen≥ 7, ﬁnd a simple graphG withn vertices,
more than 6n− 21 edges, and no K8 minor.
Thanks to Adam Hesterberg for writing the Power Round and Ian Frankel
and Paul Seymour for editing it. Thanks in advance to the graders.
7
