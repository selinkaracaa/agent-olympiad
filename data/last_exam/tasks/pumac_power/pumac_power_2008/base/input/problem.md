# PUMaC Power Round 2008

PUMaC 2008-9 Power Test
1 Forms and Landscapes
An integer-valued quadratic form is a polynomial (in two variables) of the form f (x, y) = ax2 + hxy + by2, where a,
h, and b are integers. Since this is the only type of quadratic form we are going to deal with, we will just call them
forms.
Note that f (x, y) = f (−x, −y).
A form corresponds to a landscape, which is a picture split into regions. To draw one, we start w ith these three
regions, and label them with the speciﬁed values of the form.
f(0,1)
f(1,1)
f(1,0)
Now we can expand the picture in any direction according to th e following rule: If f (x1, y1) and f (x2, y2) are in
the regions to either side of an edge, then f (x1 + x2, y1 + y2) and f (x1 − x2, y1 − y2) are in the regions on either
end. For example, in the above picture, f (0, 1) and f (1, 0) are to either side of the horizontal edge, so f (1, 1) and
f (−1, 1) are on either end. f (1, 1) is already on the right end, so f (−1, 1) is on the other end.
f(-1,1)
f(0,1)
f(1,1)
f(1,0)
Similarly, f (1, 1) and f (1, 0) are to either side of another edge, so on the opposite ends o f it are f (2, 1) and f (0, 1).
We know which end f (0, 1) is on, so f (2, 1) is on the other end:
f(-1,1)
f(0,1)
f(1,1)
f(2,1)
f(1,0)
1
Again, f (−1, 1) and f (0, 1) are on either side of an edge, so we expect to ﬁnd f (−1, 2) and f (−1, 0) on the ends.
But f (1, 0) is already on the end! This isn’t a problem, since f (−1, 0) = f (1, 0) for any form f . So, we think of
f (x, y) and f (−x, −y) as the same thing. So, f (−1, 2) (or f (1, −2)) goes on the other end:
f(-1,1)
f(-1,2)
f(0,1)
f(1,1)
f(2,1)
f(1,0)
Here it is expanded a bit:
f(-3,1)f(-2,1)f(-5,3)
f(-3,2)
f(-1,1)
f(-1,2)
f(0,1)
f(1,3)
f(2,5)
f(1,2)
f(2,3)
f(1,1)
f(2,1)
f(1,0)
It turns out that for every pair of relatively prime integers a and b, f (a, b) (or f (−a, −b)) occurs exactly once on
the landscape. You may use this fact witout proof.
2
Now taking an actual example form and ﬁlling in the values, f (x, y) = 6 x2 + 5xy −3y2, the corresponding section
of the landscape is:
361148
12
-2
-16
-3
-6
-1
4
27
8
31
6
Question 1.1: Draw the same section of the landscape for the form x2 + 2xy − 3y2
Question 1.2: Give the form for which the following is the same section of th e landscape.
21961
24
5
24
9
109
321
56
145
21
41
4
3
2 The Arithmetic Progression
Conveniently, for any form f
f (x1, y1) + f (x2, y2) = 1
2 (f (x1 + x2, y1 + y2) + f (x1 − x2, x1 − y2)) (1)
Rearranging a little, we get
(f (x1, y1) + f (x2, y2)) − f (x1 − x2, x1 − y2) =
f (x1 + x2, y1 + y2) − (f (x1, y1) + f (x2, y2))
In other words, the numbers f (x1 − x2, x1 − y2), ( f (x1, y1) + f (x2, y2)), f (x1 + x2, y1 + y2) make an arithmetic
progression.
This makes it much easier to draw landscapes. Say I start with the form f (x, y) = 3 x2 + 2xy + 4y2:
4
9
3
If I want to ﬁll in the value x to the left of the horizontal edge, I know that x, 3 + 4, and 9 make an arithmetic
progression. So, x = 5.
5
4
9
3
If I want to ﬁll in the value y to the top right, I know that 4, 3+9, and y make an arithmetic progression. So, y
must be 20.
5
4
9
20
3
The arithmetic progression shows that the values in any thre e regions which share a vertex determine the rest of
the landscape. We say that two forms are equivalent if you can line up their landscapes so that the values in the
regions are the same.
4
For example, the form f (x, y) = 6 x2 + 5xy − 3y2 and the form g(x, y) = 11 x2 + 19xy + 6y2 are equivalent. Here
are sections of their landscapes:
733688
11
12
-2
-16 -3
4
8
31
6
12
-2
-16
-3
4 8 31
6
73
36
88
11
However, if the landscape of one form is just the reﬂection of that of another, then we don’t consider the forms
to be equivalent. In particular, the forms 3 x2 − 2xy + 4x2 and 3 x2 + 2xy + 4x2 are not equivalent.
Question 2.1: Are the forms x2 + y2 and −x2 − y2 equivalent?
Question 2.2: Are the forms 3 x2 + 2xy + 4y2 and 4 x2 − 2xy + 3y2 equivalent?
Question 2.3: Are the forms 5 x2 − 5xy + y2 and x2 + xy + y2 equivalent?
Question 2.4: Are the forms 88 x2 + 113xy + 36y2 and 8 x2 − 33xy + 31y2 equivalent?
Question 2.5: Are the forms 90 x2 + 107xy + 32y2 and 101 x2 − 341xy + 288y2 equivalent?
Question 2.6: Are the forms 3 x2 − 2xy and 4 x2 − y2 equivalent?
Question 2.7: Are the forms x2 + xy − 9y2 and −x2 − xy + 9y2 equivalent?
Question 2.8: Are the forms x2 + xy − 11y2 and −x2 − xy + 11y2 equivalent?
Question 2.9: Are the forms x2 + xy − 12y2 and −x2 − xy + 12y2 equivalent?
5
3 Indeﬁnite Forms
The discriminant of a form ax2 + hxy + by2 is the value D = h2 − 4ab.
Question 3.1: Do the following numbers occur as discriminants of forms? (F or each number, if yes, give an
example, if no, prove it.) 0, 1, 2, 3, -1, -2, -3, 13, -13, 22, -2 2, 47, -47, 100, -100, 31415, -31415.
Question 3.2: Give an easy way to tell if a given integer occurs as the discri minant of a form.
Question 3.3: Prove or disprove: if two forms are equivalent, they have the same discriminant.
Question 3.4: Prove or disprove: if two forms have the same discriminant, t hey are equivalent.
We say a form is indeﬁnite if it can take on both positive and negative values. A river of a form is a connected
chain of edges on its landscape each of which separates a regi on with a positive value from a region with a negative
value, which is not a subset of any other such chain.
Question 3.5: Prove or disprove: a form is indeﬁnite if and only if it has a po sitive discriminant.
Question 3.6: Prove or disprove: every indeﬁnite form has a river.
Question 3.7: Prove or disprove: every form has at most one river.
We call a river periodic if the values to either side of it repeat. The period of a form is how many edges it takes
for it to repeat. For example, this river is periodic with per iod 6.
1
-5
-2
-5
-6
-5
-2
1
3
To make things a little more managable, we’ll draw rivers lik e this:
1 3 1
-5 -2 -5 -6 -5 -2
We call a positive integer D a periodic discriminant if there is an indeﬁnite form with discriminan t D and a
periodic river.
We call a positive integer D a nonperiodic discriminant if there is an indeﬁnite form with discriminan t D and no
periodic river.
Question 3.8: Prove or disprove: a discriminant can’t be both periodic and nonperiodic. (That is, if one
indeﬁnite form of some discriminant has a periodic river, al l indeﬁnite forms of that discriminant do.)
Question 3.9: What are the nonperiodic discriminants? Prove your answer.
Question 3.10: How many forms (up to equivalence) are there for each nonperi odic discriminant?
6
4 Symmetries
We can reﬂect the landscape of a form across or ”through” an ed ge in that landscape. For example, if we start with
this landscape, corresponding to the form 4 x2 + 2xy + 3y2:
4
-3
-17 -4 -9
1
123
The reﬂection of this landscape across the bold edge is
-17
-3
4 3 12
1
-9-4
And the reﬂection of that same landscape through the bold edge is
12
1
-9 -4 -17
-3
43
A form’s river can be symmetric in several ways. For example, the river pictured below is has two types of
symmetry. One given by reﬂection through an edge on the river (between 1 and -7); one given by reﬂection across
an edge adjacent to the river (between -3 and -3).
↔ ↔ ↔ ↔
1 2 1 2
-6 -7 -6 -3 -3 -6 -7 -6 -3 -3
The following river is symmetric in a diﬀerent way. If you rot ate the landscape around the center of the edge
between 3 and -3, and negate each value, you get the same lands cape.
7
↔ ↶ ↔
1 3 4 9 12 13 12
-12 -13 -12 -9 -4 -3 -1
We call these three types of symmetries of a river (reﬂection through an edge on the river, reﬂection across an
edge adjacent to it, and rotation around an edge on the river c ombined with negation) primitive symmetries. In the
above form, we consider the two pictured reﬂections to be the same. Both of the rivers above, then, have exactly
two primitive symmetries.
Question 4.1: Is there a periodic river with no primitive symmetries? If so , give an example, if not, prove it.
Question 4.2: Is there a periodic river with exactly one primitive symmetr y? If so, give an example, if not,
prove it.
Question 4.3: Is there a periodic river with exactly three primitive symme tries? If so, give an example, if not,
prove it.
Question 4.4: Is there a periodic river that is not equivalent to its negati on, its reﬂection, or its reﬂection’s
negation? If so, give an example. If not, prove it.
8
