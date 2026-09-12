# PUMaC Power Round 2025

PUMaC 2025 Power Round:
The Continuum Hypothesis
Zongshu Wu
Fall 2025
Rules and Reminders
1. Your solutions should be turned in by 5pm ET on Thursday , November 20th.
You will submit the solutions through Gradescope. The instructions describing how
to log into Gradescope will be sent to the coaches. The deadline for submission is
clearly visible on the Gradescope site once you enroll in the course.
Please make sure you submit your work on time, as no late submissions will be
accepted. Please do not submit your work using email or in any other way. If you
have questions about Gradescope, please post them on Piazza.
You may resubmit many times before the due date, but only your final submis-
sion will be graded . That is, the last version of the Power Round solutions that
we receive from your team will be graded.
2. Your submission must be a PDF. No other file type will be graded. You may either
typeset the solutions in LATEX, or write them by hand and scan them. In case your
solutions are handwritten, then the cover sheet (the last page of this document)
should be the first page of your submission.
We strongly encourage you to typeset the solutions. This way, the proofs will often
be more clear, and you will be less likely to lose points. You might want to use the
Solutions Template we posted.
For those new and interested in LATEX, check out Overleaf and its online guides. If
you do not know how to create a math symbol or do something in L ATEX, check out
Detexify or TeX Stack Exchange.
3. In your submission, every page should have on it the team number (not team
name) and problem number. The team number can be found by logging in to
the coach portal and selecting the corresponding team. Do not submit identifying
information aside from your team number.
Solutions to problems may span multiple pages. Please put them in order when
submitting your solutions.
4. When submitting your solutions to Gradescope, you must assign the solutions to
the correct problems on the Gradescope submission outline. Failure to do this will
result in a point deduction, as it creates a ton of extra work for us on the back-end.
5. On any problem, you may use without proof any result that is stated earlier in the
test, as well as any problem from earlier in the test, even if it is a problem that
1
your team has not solved. These are the only results you may use. In particular, to
solve a problem, you may not cite the subsequent ones.
The problems are graded separately, so you may not cite parts of your proof of
other problems. If you wish to use a lemma in multiple problems, please reproduce
the statement and proof in each problem.
6. When a problem asks you to “find”, “show”, or “prove” a result, a formal proof is
expected, in which you justify each step you take, either by using a method from
earlier or by proving that everything you do is correct. When a problem asks you
to “explain”, an informal explanation suffices.
7. All problems are numbered as “Problem x.y.z”, where x.y is the subsection number,
and z is the the number of the problem within the subsection. Each problem’s
point value is stated on the problem, and can also be found on the cover sheet.
8. Teams whose members use English as a foreign language may use dictionaries for
reference.
9. Y ou may NOT use any references, such as books or electronic resources,
except those specified in points 2 and 8. You may NOT use computer
programs, calculators, AI chatbots, or any other computational aids.
10. You may ask questions about the test on our Piazza forum. On the forum, you
may ask a public or private question. If you ask a public question, all other teams
will be able to see it. Therefore, if a public question reveals all or part of
your solution to a Power Round question, your team’s Power Round
score will be penalized severely . If your question might reveal aspects of your
solution, please ask it as a private question. On the other hand, if you are sure
that your question does not spoil anything, then we encourage you to make your
question public, so that everybody can see it.
We will post important clarifications on Piazza, and these clarifications will also be
emailed to coaches.
11. With the exception of asking questions on Piazza, communication outside your
team of 8 students about the content of these problems is prohibited.
2
Introduction and Advice
In this Power Round, we will dive into the world of axiomatic set theory , which is
the rigorous foundation for all of mathematics. We will ask and answer fundamental
questions, such as “what is a set?” If you think this question is trivial, it is not: if you’re
not careful, you run into all kinds of logical paradoxes.
Building on the foundations, we will investigate the famous Continuum Hypothesis,
which essentially asks: how large is the set R of real numbers? The answer turns out to
be quite surprising: there is no way for us to know for sure how large it is!
A large part of the difficulty in this Power Round will arise from the rigor required
when working with the formal concepts. Since we need to put everything on completely
solid footing, things that might seem obvious can often be quite nontrivial to prove. So,
it is important to make sure that your logic is airtight.
Here is some further advice with regard to the Power Round:
• Read the text of every problem! Many important ideas are included in the
problems and may be referenced later on. In addition, some of the theorems you
are asked to prove are useful or even necessary for later problems. Even if you
don’t solve a problem, you can assume its results for future problems.
• Make sure you understand the definitions! A lot of the definitions are not
easy to grasp; don’t worry if it takes you a while to fully understand them. If you
don’t, then you will not be able to do the problems. Feel free to ask clarifying
questions about the definitions on Piazza.
• Don’t make stuff up! On problems that ask for proofs, you will receive more
points if you demonstrate legitimate and correct intuition than if you fabricate
something that looks rigorous just for the sake of having “rigor”.
• Check Piazza often! Clarifications will be posted there. If you have a question,
it is possible that it has already been asked and answered in a Piazza thread. If
not, you can ask it, as long as you don’t ask a public question that reveals any part
of your solution to a problem.
• Don’t cheat! As stated in Rules and Reminders, you may NOT use any references
such as books or electronic resources (unless otherwise specified). If you cheat, you
will be disqualified and banned from PUMaC, your school may be disqualified, and
relevant external institutions may be notified of any misconduct.
Good luck, and have fun!
– Zongshu Wu, Power Round Czar
We would like to acknowledge and thank many individuals and organizations for their
support; without their help, this Power Round (and the entire competition) could not
exist. Please refer to the solutions for the Power Round for full acknowledgments and
references.
3
Contents
1 Zermelo-Fraenkel Set Theory (50 points) 6
1.1 Logical Formulas (10 points) . . . . . . . . . . . . . . . . . . . . . . . . . 6
1.2 The Axioms of ZFC (30 points) . . . . . . . . . . . . . . . . . . . . . . . . 7
1.3 Classes (10 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
1.4 Philosophical Discussion: The Meta Theory . . . . . . . . . . . . . . . . . 11
2 Ordinals (180 points) 12
2.1 The Basics of Ordinals (75 points) . . . . . . . . . . . . . . . . . . . . . . 12
2.2 Induction and Recursion (60 points) . . . . . . . . . . . . . . . . . . . . . 14
2.3 Well-Orders (45 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
2.4 Philosophical Discussion: Natural Numbers . . . . . . . . . . . . . . . . . 18
3 Cardinals (180 points) 19
3.1 The Basics of Cardinals (60 points) . . . . . . . . . . . . . . . . . . . . . . 19
3.2 Cardinal Arithmetic (60 points) . . . . . . . . . . . . . . . . . . . . . . . . 21
3.3 Cofinality (60 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
3.4 Interlude: G¨ odel’s Incompleteness Theorems . . . . . . . . . . . . . . . . . 26
4 Models of Set Theory (180 points) 28
4.1 Relativization (30 points) . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
4.2 Working in a Model (40 points) . . . . . . . . . . . . . . . . . . . . . . . . 30
4.3 The von Neumann Hierarchy (70 points) . . . . . . . . . . . . . . . . . . . 32
4.4 The Constructible Universe (40 points) . . . . . . . . . . . . . . . . . . . . 34
5 Forcing (160 points) 37
5.1 Names and Interpretation (40 points) . . . . . . . . . . . . . . . . . . . . 37
5.2 The Forcing Relation (40 points) . . . . . . . . . . . . . . . . . . . . . . . 39
5.3 Adding Cohen Reals (80 points) . . . . . . . . . . . . . . . . . . . . . . . 41
5.4 Epilogue: Towards Easton’s Theorem . . . . . . . . . . . . . . . . . . . . . 43
4
Notation
• iff: if and only if.
• ¬: ¬φ means “φ is false”.
• ∧: φ ∧ ψ means “φ and ψ”.
• ∨: φ ∨ ψ means “φ or ψ”.
• =⇒: φ =⇒ ψ means “φ implies ψ”.
• ⇐ ⇒: φ ⇐ ⇒ψ means “φ iff ψ”.
• ∀: ∀x φ(x) means “ φ(x) holds for all x”.
• ∃: ∃x φ(x) means “ φ(x) holds for some x”.
• x ∈ X means “x is an element of X” or “ X contains x”.
• (∀x ∈ X) φ(x) means ∀x (x ∈ X =⇒ φ(x)), “φ(x) holds for all x ∈ X”.
• (∃x ∈ X) φ(x) means ∃x (x ∈ X ∧ φ(x)), “φ(x) holds for some x ∈ X”.
• ∃!: ∃!x φ(x) is short for ∃x (φ(x) ∧ ∀y (φ(y) =⇒ x = y)), “φ(x) holds for exactly
one x”. Similarly, ( ∃!x ∈ X) φ(x) is short for ∃!x (x ∈ X ∧ φ(x)), “φ(x) holds for
exactly one x ∈ X”.
• ⊆: x ⊆ y is short for ( ∀z ∈ x) z ∈ y.
• {F (x) ∈ X : φ(x)} is short for {y ∈ X : ∃x (y = F (x) ∧ φ(x))}.
A Note on Rigor
In this Power Round, you may freely use any of the rules of logic, so there is no need to
be pedantic about that. Furthermore, for problems that ask you to prove things about
meta-mathematical objects (such as formulas), you may use informal arguments. After
all, we do not give rigorous definitions for meta-mathematical objects, so being rigorous
in your proofs is not even possible.
However, you must be very rigorous when proving things about sets. This is especially
important in the first section, where we build everything up from the foundations. You
are not allowed to write things like {x} or {x, y, z} or X × Y before they are introduced
(unless you define them yourself and prove that they work)!
5
1 Zermelo-Fraenkel Set Theory (50 points)
At first glance, the mathematical concept of a set could not be simpler: it is simply any
collection of things. However, after some careful thought, things start to break down. In
1901, Bertrand Russell considered the set
R = {x : x /∈ x},
consisting of all sets that don’t contain themselves. So, does R contain itself? Well, by
definition, R contains R if and only if R does not contain R! This paradox, known as
Russell’s paradox, indicates that something is wrong with our na ¨ ıve notion of sets.
The only way to resolve this paradox is to declare that R does not exist – that there is
no set consisting of precisely those sets that don’t contain themselves. In other words,
we need to part ways with the idea that any collection of things can be a set.
Since we can’t make the assumption that any collection forms a set, we instead make
a different (and much more complicated) list of assumptions in order to work with sets.
These are known as the axioms of Zermelo-Fraenkel set theory (ZFC), named after Ernst
Zermelo and Abraham Fraenkel, who developed it in the early 20th century.
1.1 Logical Formulas (10 points)
Before we get started, we need to say some words about how mathematical logic works
in the world of axiomatic set theory. Read this part carefully!
In set theory, sets are the only kind of mathematical object. Everything is a set. To
talk about sets, we use formulas.
Definition 1.1.1 — A formula (in set theory) is a statement about sets, involving
some number of variables, which represent sets. If a formula explicitly depends on a
variable, then the variable is called free. Otherwise, the variable is called bound. If a
formula has no free variables, then it is called a sentence.
The expression φ(x1, x2, . . . , xn) refers to some formula whose free variables are
among x1, x2, . . . , xn. (It might be the case that some of the variables xi are bound,
or do not occur in the formula at all.)
By itself, this definition probably doesn’t make a whole lot of sense, so we give many
examples to illustrate what it means.
• x ∈ y is a formula with two free variables, x and y. The meaning of this statement
depends on what sets we substitute in place of x and y.
• ∃x (x = y) is a formula with one free variable, y, and one bound variable, x. The
meaning of this statement depends on y, but it does not depend on x, because x is
just a dummy variable without an actual value assigned to it. Instead, we say that
we are quantifying over x using the symbol ∃.
• ∀x (¬x ∈ x) has no free variables, so it is a sentence. Similarly, we are quantifying
over x using the symbol ∀.
• x ∈ y ∧ ∀x (y ∈ x) is... erm... is x free or bound?? It is free in its first occurrence,
but bound in its later occurrences. Such cursed situations are technically allowed
in logic, but for obvious reasons, it is a very bad idea to write formulas like this, so
we will assume that this never happens.
6
Any formula can be written in terms of the symbols = (equality), ∈ (set membership),
and the logical symbols ¬, ∧, ∨, ⇒, ⇔, ∀, ∃ defined in the Notation section. Usually, we
will abbreviate formulas using other symbols, such as ⊆. For instance, we can abbreviate
(∀z ∈ x) z ∈ y as x ⊆ y.
Notice that when performing such abbreviations, bound variables can disappear, but
the free variables don’t change. In the example above, after we abbreviate the formula,
the bound variable z disappears, but the free variables are x and y regardless.
Problem 1.1.1 (10 points)
Show that every formula is equivalent to one that only uses = , ∈, ¬, ∧, ∃.
Formulas are not considered mathematical objects in set theory, because they are not
sets! In particular, in a formula, we can never quantify over a formula, so something like
“there exists a formula such that ...” cannot be written as a formula. Instead, formulas
are meta-mathematical objects – overlords that govern the mathematical world of sets.
1.2 The Axioms of ZFC (30 points)
We now describe the axioms of ZFC, a list of sentences that we assume when we prove
anything about sets. They are written in natural language here, but it is possible (you
can try) to write them using only = , ∈, ¬, ∧, ∨, ⇒, ⇔, ∀, ∃. But of course, that would be
quite cumbersome, so we won’t do that here.
Axiom (Extensionality)
Two sets x, yare equal iff z ∈ x ⇐ ⇒z ∈ y for any set z.
Axiom (Pairing)
Given two sets x, y, there exists a set {x, y} such that z ∈ {x, y} iff z = x or z = y.
Axiom (Union)
Given a set X, there exists a set S X such that y ∈ S X iff y ∈ x for some x ∈ X.
Axiom (Power Set)
Given a set X, there exists a set P(X) such that A ∈ P(X) iff A ⊆ X.
Axiom (Separation)
Let φ(x, p1, . . . , pn) be any formula. Given a set X and some parameters p1, . . . , pn,
there exists a set Y such that x ∈ Y iff x ∈ X and φ(x, p1, . . . , pn). This set Y is
denoted {x ∈ X : φ(x, p1, . . . , pn)}.
The axiom of separation is not a single axiom; instead, it is an axiom schema , which
means that it consists of infinitely many axioms, one for every formula φ(x, p1, . . . , pn).
(In particular, ZFC has infinitely many axioms.)
7
Before we introduce the rest of the axioms (three axioms and one axiom schema), we
take some time to see what we can do already with what we have.
Problem 1.2.1 (5 points)
Given a nonempty set X, prove that there exists a set T X such that y ∈ T X iff
y ∈ x for all x ∈ X.
Problem 1.2.2 (5 points)
Given two sets x, y, prove the existence of the following sets:
(a) The set {x}, such that z ∈ {x} iff z = x;
(b) The set x ∪ y, such that z ∈ x ∪ y iff z ∈ x or z ∈ y;
(c) The set x ∩ y, such that z ∈ x ∩ y iff z ∈ x and z ∈ y.
In particular, given x1, . . . , xn, we may form the set {x1, . . . , xn} = {x1} ∪ · · · ∪ {xn},
such that y ∈ {x1, . . . , xn} iff y = xi for some i.
Next, we formally define the notion of ordered pairs in terms of sets. This definition is
due to Kazimierz Kuratowski.
Definition 1.2.1 — For two sets x, y, define the ordered pair (x, y) = {{x}, {x, y}}.
Problem 1.2.3 (5 points)
Prove that (x, y) = (z, w) iff x = z and y = w.
Problem 1.2.4 (5 points)
Given two sets X, Y, show that we can form the set X × Y of ordered pairs ( x, y)
where x ∈ X and y ∈ Y , called the Cartesian product of X and Y .
Ordered pairs allow us to define what relations and functions are.
Definition 1.2.2 — A relation is a set R consisting of ordered pairs. We usually
write x R yas a shorthand for ( x, y) ∈ R.
A relation f is a function if, for any set x, there is at most one set y such that
(x, y) ∈ f . If such a y exists, then we write f (x) = y.
Problem 1.2.5 (5 points)
Let R be a relation. Show that we can form the sets
dom(R) = {x : ∃y (x, y) ∈ R} and ran( R) = {y : ∃x (x, y) ∈ R},
called the domain and range of R, respectively.
8
Definition 1.2.3 — A relation R is said to be on X if R ⊆ X × X. A function f is
said to be on X if dom(f ) = X. A function f is said to be from X to Y , written
f : X → Y , if dom( f ) = X and ran(f ) ⊆ Y .
Definition 1.2.4 — A function f : X → Y is called injective/surjective/bijective,
or a(n) injection/surjection/bijection, if for any y ∈ Y , there is at most one/at least
one/exactly one x ∈ X such that f (x) = y.
Definition 1.2.5 — Let f be a function. The restriction of f to X is the function
f ↾X = {(x, y) ∈ f : x ∈ X}. The image of X under f is f ′′X = ran(f ↾X).
These definitions and results might be familiar from “normal math” – all we did was
make everything rigorous using our set-theoretic framework. We now introduce the rest
of the axioms of ZFC.
Axiom (Infinity)
There exists a set ∅ that contains nothing. Furthermore, there exists a set I such
that ∅ ∈ I, and if x ∈ I, then x ∪ {x} ∈I.
Axiom (Replacement)
Let φ(x, y, p1, . . . , pn) be any formula, and fix some parameters p1, . . . , pn. If
φ(x, y, p1, . . . , pn) ∧ φ(x, z, p1, . . . , pn) = ⇒ y = z
holds for all x, y, z, then given any set X, there exists a set Y such that y ∈ Y iff
φ(x, y, p1, . . . , pn) for some x ∈ X.
Axiom (Regularity)
Any nonempty set X contains an element x, called an ∈-minimal element , such that
y /∈ x for any y ∈ X.
Axiom (Choice)
Let X be a set. If all elements of X are nonempty, then there exists a function f on
X, called a choice function, such that f (x) ∈ x for all x ∈ X.
Just like the axiom of separation, the axiom of replacement is also an axiom schema
consisting of infinitely many axioms.
Problem 1.2.6 (5 points)
Prove that no set contains itself, and no two sets contain each other.
9
1.3 Classes (10 points)
Not every collection of sets is a set. As you have already seen in the previous problems,
when we want to define a set like X × Y , we can’t just say
X × Y = {(x, y) : x ∈ X ∧ y ∈ Y };
instead, we need to prove that such a desired collection of sets actually exists using the
axioms of ZFC. But what if we still want to talk about arbitrary collections of sets? For
this, we introduce the notion of a class.
Definition 1.3.1 — Let φ(x, p1, . . . , pn) be a formula. Given parameters p1, . . . , pn,
we shall sometimes write x ∈ {x : φ(x, p1, . . . , pn)} in place of φ(x, p1, . . . , pn). The
expression {x : φ(x, p1, . . . , pn)} is called a class.
Intuitively, a class C = {x : φ(x, p1, . . . , pn)} is the “collection” of sets satisfying the
property φ(x, p1, . . . , pn). Classes are not sets; we introduce them simply because they
are a convenient and intuitive notational shorthand.
Definition 1.3.2 — Let C and D be two classes. We say that C is a subclass of D,
denoted C ⊆ D, if x ∈ C =⇒ x ∈ D for all x. We say that C is equal to D, denoted
C = D, if x ∈ C ⇐ ⇒x ∈ D for all x.
Definition 1.3.3 — A class C is a set if, for some set X, we have C = {x : x ∈ X}
(that is, x ∈ C ⇐ ⇒x ∈ X for all x). A class that is not a set is called a proper class.
By the axiom of extensionality, if such a set X exists, then it must be unique. Notice
that saying “C is a set” is an abuse of terminology – classes are not actually sets! We do
this because it just makes everything more convenient. If you pay attention to what you
are doing, then there shouldn’t be any issues.
In fact, if C = {x : x ∈ X}, then we will pretend as if C and X are the same thing.
Under this convention, every set X “is” a class (namely, the class {x : x ∈ X}), and we
can rephrase the axiom of separation as: any subclass of a set is a set .
Definition 1.3.4 — The universe is the class V = {x : x = x} of all sets.
Problem 1.3.1 (5 points)
Show that the universe V is a proper class.
Many (but not all!) of the concepts we defined for sets work for classes as well. You
should be able to guess how the definitions go before looking at them:
Definition 1.3.5 — Let C and D be classes. Define the following classes:
C ∪ D = {x : x ∈ C ∨ x ∈ D}, S C = {x : (∃X ∈ C) x ∈ X},
C ∩ D = {x : x ∈ C ∧ x ∈ D}, T C = {x : (∀X ∈ C) x ∈ X},
C × D = {(x, y) : x ∈ C ∧ y ∈ D}.
10
In fact, if C is nonempty, then T C is always a set. This can be proved similarly to
Problem 1.2.1. (For the empty class, we have T ∅ = V .)
Definition 1.3.6 — A class relation is a class of ordered pairs. For a class relation
R, we write x R yto mean ( x, y) ∈ R. A class relation on a class C is a subclass of
C × C. Given a class relation R, define the classes
dom(R) = {x : ∃y (x, y) ∈ R} and ran( R) = {y : ∃x (x, y) ∈ R}.
A class relation F is a class function if, for any set x, there is at most one set y
such that (x, y) ∈ F . A class function F is on a class C if dom(F ) = C, and from
C to D, written F : C → D, if dom(F ) = C and ran(F ) ⊆ D. The restriction of a
class function F to a class C is the class function F ↾C = {(x, y) ∈ F : x ∈ C}, and
the image of C under F is F ′′C = ran(F ↾C).
The following problem is a convenient rephrasing of the axiom of replacement.
Problem 1.3.2 (5 points)
Let F be a class function, and suppose that dom(F ) is a set. Prove that ran(F ) is a
set, and conclude that F is also a set.
1.4 Philosophical Discussion: The Meta Theory
In the previous problems, you used the axioms of ZFC to prove many statements – that
is, sentences. However, if you look carefully, you might notice that some of the problem
statements aren ’tsentences. Notably, Problem 1.3.2 starts by picking an arbitrary class
function F , which is not allowed in a sentence (as classes are not sets). So, what did you
actually do by solving the problem?
Recall that the axioms of separation and replacement are actually axiom schemata: 1
they consist of infinitely many axioms. Similarly, we may think of solving Problem 1.3.2
as proving infinitely many sentences at once: for every class F , you prove the sentence
that if F is a class function and dom( F ) is a set, then ran( F ) and F are sets.
That is, the statement of Problem 1.3.2 is a meta-mathematical statement, instead
of a mathematical statement (i.e. a formula). To clarify this distinction, we introduce
the terms base theory and meta theory. Sets live in the base theory, and when we prove
sentences, we are working in the base theory. In contrast, meta-mathematical objects,
like formulas or classes, live in the meta theory, and reasoning about them constitutes
working in the meta theory.
For most problems in this Power Round, the distinction between the base theory and
the meta theory can be mostly handwaved away. However, if you are not careful, you
might still make mistakes! It is especially important to keep this in mind in the later
sections, as there will be a blend of mathematical and meta-mathematical concepts.
Finally, if you are worried about the abuse of terminology where we say that certain
classes “are” sets, rest assured that this will not cause any problems. Every time such an
abuse of terminology occurs, it is always possible to rewrite things such that the abuse
does not occur, often with the expense of making everything more cumbersome.
1The plural form of “schema”.
11
2 Ordinals (180 points)
Ordinals are one of the most important concepts in set theory. Intuitively, they give us a
way of counting past infinity. The natural numbers 0 , 1, 2, . . .are ordinals,2 but beyond
that, we have the ordinal ω, the smallest infinite ordinal. After that, we have ω + 1, then
ω + 2, and so on, then ω + ω = ω · 2, and on and on and on...
As sets, each ordinal α is, intuitively, the set of ordinals smaller than α. For instance,
since there are no ordinals less than 0, we have 0 = ∅. Next, we have 1 = {0} = {∅},
and 2 = {0, 1} = {∅, {∅}}, and then ω = {0, 1, 2, . . .}, and ω + 1 = {0, 1, 2, . . . , ω}, and
so on and so forth. This informal idea will be made rigorous below.
2.1 The Basics of Ordinals (75 points)
Definition 2.1.1 — A class x is transitive if any element of x is a subclass of x.
In other words, if x is transitive, then z ∈ y and y ∈ x imply z ∈ x. For example, the
sets ∅ and {∅, {∅}, {{∅}}} are transitive, but {{∅}} is not transitive.
Definition 2.1.2 — A set α is an ordinal if α is transitive, and every element of α
is also transitive. The class of ordinals is denoted Ord.
For example, ∅ and {∅, {∅}} are ordinals, but {∅, {∅}, {{∅}}} (a transitive set) is
not an ordinal, because it contains an element {{∅}} which is not transitive.
Problem 2.1.1 (5 points)
Show that any element of an ordinal is an ordinal.
Problem 2.1.2 (10 points)
Let C be a class of ordinals. Show that if C is a set, then S C is an ordinal, and
show that if C is nonempty, then T C is an ordinal. Conclude that if α and β are
ordinals, then α ∪ β and α ∩ β are also ordinals.
Problem 2.1.3 (20 points)
Let α be an ordinal, and let x, ybe distinct elements of α. Prove that either x ∈ y
or y ∈ x. (Hint: use the axiom of regularity.)
Problem 2.1.4 (15 points)
Let α and β be ordinals. Prove that α ⊆ β iff α ∈ β or α = β.
Problem 2.1.5 (10 points)
Let α and β be distinct ordinals. Prove that either α ∈ β or β ∈ α.
2In set theory, 0 is considered a natural number.
12
Using the previous two problems, we can easily see that for any two ordinals α and β
(not necessarily distinct), we have α ⊆ β or β ⊆ α.
Definition 2.1.3 — Let α and β be ordinals. We write α < βor β > αfor α ∈ β,
and write α ≤ β or β ≥ α for α ⊆ β.
The results that we have shown so far imply that this method of comparing ordinals
works exactly as you’d expect it to. For example, we have α ≤ β iff α < β∨ α = β iff
α ̸> β. We can also combine inequalities: for instance, if α < β < γ, then α < γ, and if
α ≤ β ≤ γ, then α ≤ γ. From now on, you may freely use the basic properties of ordinal
comparison without proof.
Problem 2.1.6 (10 points)
Let C be a class of ordinals. Show that
(a) If C is a set, then S C is the smallest ordinal which is greater than or equal to
all elements of C.
(b) If C is nonempty, then T C is the smallest element of C.
Definition 2.1.4 — Let C be a class of ordinals. If C is a set, then its supremum is
sup C = S C. If C is nonempty, then its minimum is min C = T C.
The axiom of regularity implies that any nonempty set of ordinals contains a smallest
element, but the previous problem generalizes this statement to any nonempty class of
ordinals, and also explicitly tells us what the minimum is!
Definition 2.1.5 — The successor of an ordinal α is the set S(α) = α ∪ {α}.
Problem 2.1.7 (5 points)
Prove that S(α) is the least ordinal greater than α.
Using the successor function, we can define
0 = ∅,
1 = S(0) = {∅},
2 = S(1) = {∅, {∅}},
3 = S(2) = {∅, {∅}, {∅, {∅}}},
4 = S(3) = {∅, {∅}, {∅, {∅}}, {∅, {∅}, {∅, {∅}}}},
and so on. It quickly becomes unwieldy to expand everything out completely: using the
notation above, writing the number n in full requires 2 n+1 − 1 symbols. Figure 1 shows
how tedious it can be even for relatively small numbers.
Warning: this is not a rigorous definition of a natural number! You might think that
we can define a natural number as “the result of applying S finitely many times to 0”,
but this is circular logic, because we need natural numbers in order to formalize what
“finite” means. In the next subsection, we will define natural numbers properly.
13
Figure 1: A visual representation of the number 8.
2.2 Induction and Recursion (60 points)
In this subsection, we will define the natural numbers, and rigorously justify induction
and recursion. In “normal” math, we say “recursive definition” and “inductive definition”
interchangeably, but in fact, recursion does not trivially follow from induction, and we
need to do some work to justify recursion. (See Problem 2.2.6.)
Definition 2.2.1 — An ordinal α is called a successor ordinal if α = S(β) for some
ordinal β. A limit ordinal is a nonzero ordinal which is not a successor ordinal.
The ordinal 0 = ∅ is the only ordinal which is neither a successor nor a limit ordinal,
just like how 1 is the only positive integer which is neither prime nor composite.
Problem 2.2.1 (5 points)
Show that a nonzero ordinal α is a limit ordinal iff α = sup{β : β < α}. (Note that
{β : β < α} is another way of writing the set α.)
Definition 2.2.2 — An ordinal n is a natural number if every ordinal k less than or
equal to n is either 0 or a successor ordinal.
It is not hard to see that if n is a natural number, then S(n) is a natural number, and
every k ≤ n is a natural number. We now prove that mathematical induction works.
Problem 2.2.2 (10 points)
Let C be a class. Suppose that 0 ∈ C, and if n ∈ C for a natural number n, then
S(n) ∈ C. Prove that C contains all natural numbers.
Problem 2.2.3 (10 points)
Prove that we can form a set ω such that n ∈ ω iff n is a natural number, and show
that ω is the least limit ordinal.
In fact, we can prove a vast generalization of the principle of mathematical induction,
known as transfinite induction, which works for all ordinals.
14
Problem 2.2.4 (5 points)
Let C be a class. Suppose that if α is an ordinal, and β ∈ C for every β < α, then
α ∈ C. Prove that C contains all ordinals.
Often, transfinite induction is split into three cases, depending on whether α is 0, a
successor ordinal, or a limit ordinal.
Problem 2.2.5 (10 points)
Let C be a class. Suppose that
• 0 ∈ C;
• If α ∈ C, then S(α) ∈ C;
• If α is a limit ordinal, and β ∈ C for all β < α, then α ∈ C.
Prove that C contains all ordinals.
We can use transfinite induction to recursively define class functions on Ord. If we
want to define a class function F on Ord, then it suffices to define F (α) in terms of the
values of F (β) for β < α. This is known as transfinite recursion, and the next problem
will ask you to justify it rigorously.
Problem 2.2.6 (15 points)
Let G be a class function on the universe V . Find a class function F on Ord such
that F (α) = G(F ↾α) for every ordinal α, and show that any two such class functions
are equal. (Note that F ↾α is a set by Problem 1.3.2.)
Just like transfinite induction, we usually split transfinite recursion into three cases:
zero, successor, and limit. To give a simple example, let α be an ordinal, and let Gα be
the class function on V defined as
Gα(f ) =



α if f = ∅,
S(f (β)) if f : S(β) → Ord,
sup(ran(f )) if f : β → Ord for a limit ordinal β,
∅ otherwise.
Applying transfinite recursion, we get a class function Fα on Ord such that Fα(0) = α,
Fα(S(β)) = S(Fα(β)), and Fα(β) = sup{Fα(γ) : γ < β} for limit ordinals β. Finally, we
denote α + β = Fα(β). We’ve just defined ordinal addition!
This definition may be cleanly summarized as follows:
Definition 2.2.3 — Define the sum α + β of two ordinals recursively as
• α + 0 = α,
• α + S(β) = S(α + β),
• α + β = sup{α + γ : γ < β}, if β is a limit ordinal.
15
Let’s look at some examples. Firstly, we have
1 + 1 = 1 +S(0) = S(1 + 0) = S(1) = 2.
And in general, we have α + 1 = S(α), and α + 2 = S(S(α)), etc., by definition. These
facts are intuitive, but sometimes, weird things can happen. For instance,
1 + ω = sup{1 + n : n < ω} = ω ̸= ω + 1,
so ordinal addition is not commutative! (Ordinal addition is associative: ( α + β) + γ =
α + (β + γ) for all ordinals α, β, γ, but this is quite tricky to prove.)
Problem 2.2.7 (5 points)
Prove that if β is a limit ordinal, then α + β is also a limit ordinal.
Similarly, we can define ordinal multiplication.
Definition 2.2.4 — Define the product α · β of two ordinals recursively as
• α · 0 = 0,
• α · S(β) = α · β + α,
• α · β = sup{α · γ : γ < β}, if β is a limit ordinal.
For example, we have α · 1 = α · S(0) = α · 0 + α = 0 + α = α. Next, α · 2 = α + α,
and then α · 3 = α + α + α, and so on, by definition.
Just like ordinal addition, ordinal multiplication is associative: ( α · β) · γ = α · (β · γ),
but not commutative: we have ω · 2 = ω + ω, but 2 · ω = sup{2n : n < ω} = ω. Ordinal
multiplication also satisfies a distributive law: α · (β + γ) = α · β + α · γ. However, it is
not always true that ( α + β) · γ = α · γ + β · γ. (Take α = β = 1 and γ = ω.)
We can go further: ordinal exponentiation may be defined in a similar way as ordinal
multiplication. But we won’t go into that in this Power Round.
2.3 Well-Orders (45 points)
In addition to letting us “count past infinity”, ordinals are useful in set theory because
they allow us to quantify a special kind of ordering, called a well-order.
Definition 2.3.1 — Let X be a set. A relation < on X is a partial order if
(1) x < xis false for every x ∈ X, and
(2) x < yand y < zimplies x < zfor all x, y, z∈ X.
The relation < is a well-order if, in addition, we have
(3) x < yor x = y or y < xfor all x, y∈ X, and
(4) Any nonempty A ⊆ X contains some m such that x ̸< mfor all x ∈ A.
A poset (short for partially ordered set ) is a pair ( X, <), where < is a partial order
on X. A poset ( X, <) is a well-ordered set if < is a well-order on X.
16
For example, consider the relation {(A, B) ∈ P(X) × P(X) : A ⊊ B} on P(X), which
we will abbreviate as just “ ⊊”. Then, ( P(X), ⊊) is a poset. But, if X has more than 1
element, then ⊊ is not a well-order on P(X), because it fails condition (3).
For another (very important) example, let α be an ordinal, and consider the relation
{(x, y) ∈ α × α : x ∈ y} on α, which we will abbreviate as just “ ∈”. Then, the problems
in Section 2.1 tell us that ( α, ∈) is a well-ordered set.
Definition 2.3.2 — Let (X, <X ) and ( Y, <Y ) be two well-ordered sets. A function
f : X → Y is called an order-isomorphism if it is a bijection, and for all x, y∈ X, if
x <X y, then f (x) <Y f (y). If there exists an order-isomorphism f : X → Y , then
we say that ( X, <X ) and ( Y, <Y ) are isomorphic, denoted ( X, <X ) ∼= (Y, <Y ), or, if
the context is clear, simply X ∼= Y .
You can think of “isomorphic” as meaning “basically the same”. For instance, consider
the following two well-ordered sets:
(X, <X ) = ({a, b, c}, {(a, b), (a, c), (b, c)}),
where a <X b <X c, and
(Y, <Y ) = ({p, q, r}, {(p, q), (r, p), (r, q)}),
where r <Y p <Y q. Then, the structures of the two well-ordered sets are pretty much
identical: in both cases, we have a chain of three elements in increasing order. Indeed, the
function f : X → Y given by f (a) = r, f (b) = p, and f (c) = q is an order-isomorphism,
and thus, the two well-ordered sets are isomorphic.
Problem 2.3.1 (10 points)
Let (X, <X ), (Y, <Y ), and ( Z, <Z) be well-ordered sets. Show that
(a) X ∼= X.
(b) If X ∼= Y , then Y ∼= X.
(c) If X ∼= Y and Y ∼= Z, then X ∼= Z.
Problem 2.3.2 (15 points)
Let (X, <) be a well-ordered set. Prove that there exists a unique ordinal α, called
the order type of (X, <), such that ( X, <) ∼= (α, ∈).
Problem 2.3.3 (20 points)
Prove that for any set X, there exists a bijection f from X to some ordinal α, and
conclude that there exists a well-order on X. (Hint: use the axiom of choice.)
This problem establishes the well-ordering theorem: every set can be well-ordered. It
was first proven by Ernst Zermelo in 1904. The axiom of choice (often abbreviated as
AC) is crucial in proving the well-ordering theorem. If your solution didn’t use it, then it
is wrong! In fact, if we work in ZF, which is ZFC without choice, then we can prove that
17
AC is equivalent to the well-ordering theorem. (Problem 2.3.3 establishes one direction:
AC implies the well-ordering theorem. You are welcome to try the other direction, but
we won’t need this result.)
Many set theorists see the well-ordering theorem as somewhat unintuitive. It states
that all sets can be well-ordered, including, for instance, R.3 How would you well-order
R? It’s not something you can write down explicitly (without using AC), and the field of
descriptive set theory , which studies R from a set-theoretic perspective, tells us that such
a well-order would have bizarre properties. There is a famous joke by Jerry Bona:
The axiom of choice is obviously true, the well-ordering principle
obviously false, and who can tell about Zorn ’s lemma?
(Zorn ’s lemma is another result equivalent to the axiom of choice, and it is used in many
areas of mathematics, but it has a rather complicated statement.)
2.4 Philosophical Discussion: Natural Numbers
In this section, we spent a lot of effort defining what natural numbers are, and making
sure that the logic is completely airtight. However, if you look carefully, you may notice
that we have actually been secretly using natural numbers since the very beginning of
this Power Round! For instance, when we wrote “let φ(x, p1, . . . , pn) be a formula”, we
were invoking the concept of natural numbers, as n is a natural number. Did we commit
the error of using a concept before defining it?
Don’t worry – we didn’t. When we write something like φ(x, p1, . . . , pn), the number
n lives in the meta theory, instead of the base theory. It is a “meta natural number”, if
you will. So, we were using meta natural numbers in the meta theory, before defining
natural numbers in the base theory. This is not circular reasoning!
But things still feels a bit suspicious. If we need meta natural numbers to formalize
natural numbers, then we can ask: where do the meta natural numbers come from? We
would need a “meta meta theory” to formalize the meta natural numbers, and a “meta
meta meta theory” to formalize that, and so on. Turtles all the way down. And the issue
is not just with natural numbers. If we want to formalize logic, then we would need a
logical system in which to do so.
It seems that an infinite regress is unavoidable. In practice, logicians and set theorists
deal with this problem by ignoring it. After all, we have to start somewhere. Instead
of getting stuck in a fruitless cycle of formalization, we choose the meta theory as our
starting point, and take it for granted. (In particular, there will be no such thing as a
“meta meta theory”.) From there, we can specify the basic rules of logic, and list out the
axioms of the base theory ZFC.
In fact, we can go further, and formalize a copy of ZFC inside the base theory! To do
logic within our set-theoretic framework, we encode each formula φ as a natural number
⌜φ⌝, called the G¨ odel numberof φ (named after Kurt G¨ odel), and formalize all of the
rules of logic within the base theory. Finally, we write down the G¨ odel numbers of the
axioms of ZFC. The resulting set of G¨ odel numbers is called the coded theory.
The coded theory can be thought of as a copy of ZFC, inside the base theory ZFC, and
one level “below” the base theory. In an abuse of notation, the coded theory is usually
also denoted ZFC, but we shall write ⌜ZFC⌝ to avoid confusion.
3We won’t give a precise definition of R in this Power Round.
18
3 Cardinals (180 points)
Infinite sets behave quite differently than finite sets, as famously illustrated in David
Hilbert’s Grand Hotel. Imagine a hotel with infinitely many rooms, numbered 0 , 1, 2, . . .,
each occupied by a guest, say, Room n is occupied by Guest n. The hotel is full, and yet,
it can accommodate more guests: by moving Guest n to Room n + 1 for all n, Room 0
is left vacant for a new guest, say Guest ω, to move into. In other words, the two sets
ω = {0, 1, 2, . . .} and ω + 1 = {0, 1, 2, . . . , ω} have the same “size”, in some sense, even
though ω is a proper subset of ω + 1.
But are there any infinite sets that have a larger size than ω? In 1874, Georg Cantor
answered this question in the affirmative: he proved that the set R of real numbers has
strictly more elements than ω. If a guest for every real number came to Hilbert’s Hotel,
then the hotel would not be able to accommodate everyone.
More precisely, the size of a set X is measured by its cardinality |X|, a special kind of
ordinal called a cardinal. For example, the cardinality of {a, b, c} is 3, because {a, b, c}
has 3 elements, and the cardinalities of ω and ω + 1 are ℵ0 = ω, which is the smallest
infinite cardinal. After ℵ0, the next cardinal is ℵ1, and then ℵ2, and after infinitely many
of these, we reach ℵω. In fact, there is a cardinal ℵα for every ordinal α.
All of the informal ideas above will be made fully rigorous in what follows.
3.1 The Basics of Cardinals (60 points)
Definition 3.1.1 — Two sets X and Y are equinumerous, denoted X ≈ Y , if there
exists a bijection f : X → Y .
For example, we have already seen that ω and ω + 1 are equinumerous. It is also not
hard to show that ω and ω · 2 are equinumerous: we can define a bijection f : ω · 2 → ω
via f (n) = 2n and f (ω + n) = 2n + 1, where n < ω.
Problem 3.1.1 (5 points)
Let X, Y, Zbe sets. Show that
(a) X ≈ X.
(b) If X ≈ Y , then Y ≈ X.
(c) If X ≈ Y and Y ≈ Z, then X ≈ Z.
The well-ordering theorem (Problem 2.3.3) tells us that any set X is equinumerous to
at least one ordinal, so we can use ordinals to measure the sizes of sets.
Definition 3.1.2 — The cardinality of a set X, denoted |X|, is the smallest ordinal
α such that X ≈ α. An ordinal κ is a cardinal if |κ| = κ (in other words, if κ is not
equinumerous to a smaller ordinal).
A set X is finite if |X| < ωand infinite if |X| ≥ω. An infinite set X is countable
if |X| = ω, and uncountable if |X| > ω.
The cardinality of a set is always a cardinal. Indeed, we have X ≈ |X|, so if |X| were
equinumerous to some smaller ordinal α, then X would also be equinumerous to α, but
this would contradict the definition of |X|.
19
Problem 3.1.2 (5 points)
Prove that every infinite cardinal is a limit ordinal.
Problem 3.1.3 (20 points)
Let X and Y be sets. Prove that
(a) |X| ≤ |Y | iff there exists an injection f : X → Y .
(b) |X| ≥ |Y | iff there exists a surjection f : X → Y , assuming Y is nonempty.
(c) |X| = |Y | iff there exists a bijection f : X → Y (that is, X ≈ Y ).
Problem 3.1.4 (10 points)
Prove that every natural number is a cardinal.
Problem 3.1.5 (5 points)
Prove that if X is a set of cardinals, then sup X is a cardinal. In particular, show
that ω is a cardinal.
The previous problem ensures that countable sets exist: the set ω is countable, since
|ω| = ω. Of course, ω + 1 and ω · 2 are also countable. The existence of uncountable sets
follows from Cantor’s theorem, named after Georg Cantor.
Theorem 3.1.3 (Cantor)
If X is a set, then |X| < |P(X)|.
Proof. Suppose for the sake of contradiction that |X| ≥ |P(X)|. Then by Problem 3.1.3,
there exists a surjective function f : X → P(X). Now consider the set
A = {x ∈ X : x /∈ f (x)} ∈ P(X).
We have A = f (x) for some x ∈ X. But then x ∈ A iff x /∈ A, a contradiction.
In particular, P(ω) is uncountable. It is not too hard to show that R is equinumerous
to P(ω), so R is also uncountable. (Our proof of this is not Cantor’s original 1874 proof;
instead, it is essentially equivalent to another proof he gave in 1891.)
Cantor’s theorem implies that there is no largest cardinal: indeed, if κ is a cardinal,
then the cardinal |P(κ)| is always strictly larger than κ. Thus, we define:
Definition 3.1.4 — Define the aleph numbers ℵα (also denoted ωα) recursively as
• ℵ0 = ω,
• ℵα+1 is the smallest cardinal greater than ℵα,
• ℵα = sup{ℵβ : β < α}, if α is a limit ordinal.
20
Problem 3.1.6 (15 points)
Prove that every infinite cardinal is equal to ℵα for some ordinal α.
3.2 Cardinal Arithmetic (60 points)
Before we begin, here is a basic definition.
Definition 3.2.1 — Let I be a set and C be a class. A family of elements of C,
indexed by I, is a function x : I → C. In this context, we write xi in place of x(i)
and (xi)i∈I in place of x.
In elementary school, the basic operations of arithmetic are introduced by studying
what we would call the cardinality of finite sets. For example, the equality 1 + 1 = 2 is
usually interpreted to mean that if two disjoint sets {a} and {b} have cardinality 1, then
the union {a} ∪ {b} = {a, b} has cardinality 2. Building on this idea, we define the sum
of any number of cardinals.
Definition 3.2.2 — Let (Xi)i∈I be a family of sets. Their union S
i∈I Xi is defined
as S ran(X) = {x : (∃i ∈ I) x ∈ Xi}, and their disjoint union F
i∈I Xi is defined as
the union S
i∈I Xi × {i}. If we only have two sets X, Y, then we write their disjoint
union as X ⊔ Y = (X × {0}) ∪ (Y × {1}).
For a family (κi)i∈I of cardinals, their sum P
i∈I κi is defined as
F
i∈I κi
. If we
only have two cardinals κ, λ, then we write their sum as κ + λ = |κ ⊔ λ|.
Intuitively, the disjoint union takes a family ( Xi)i∈I of sets, and replaces each set Xi
with Xi × {i} to ensure that the sets are disjoint, before taking the union.
Problem 3.2.1 (10 points)
Show that
S
i∈I Xi
 ≤ P
i∈I |Xi|, with equality if the Xi are pairwise disjoint, that
is, Xi ∩ Xj = ∅ for i ̸= j ∈ I. (Hint: if you think this is trivial, you are probably
missing something.)
Cardinal addition satisfies many of the properties you would expect addition to satisfy.
It is associative: ( κ + λ) + µ = κ + (λ + µ), commutative: κ + λ = λ + κ, increasing:
λ ≤ µ implies κ + λ ≤ κ + µ, and finally, κ + 0 = κ. These facts can be easily shown
using the previous problem.
Warning: cardinal addition is not the same thing as ordinal addition, even though we
use the symbol + for both! For example, let’s compute ℵ0 + 1, where + means cardinal
addition. Since |ω| = ℵ0 and |{ω}| = 1, and the sets ω and {ω} are disjoint, we have
ℵ0 + 1 = |ω ∪ {ω}| = |ω + 1| = ℵ0.
That is, ℵ0 + 1 (where + is cardinal addition) is not equal to ω + 1 (where + is ordinal
addition). To prevent confusion, we will adopt the following convention:
• When thinking of ℵα = ωα as the cardinality of some set (e.g. when doing cardinal
arithmetic), we write ℵα.
• When thinking of ℵα = ωα as an ordinal that just so happens to be a cardinal (e.g.
when doing ordinal arithmetic), we write ωα (or simply ω if α = 0).
21
Anyways, it should almost always be clear from context whether + is supposed to stand
for ordinal addition or cardinal addition.
Next, we turn our attention to multiplication. In elementary school arithmetic, the
equality 2 · 3 = 6 means that if {a, b} has cardinality 2 and {x, y, z} has cardinality 3,
then their Cartesian product {a, b} × {x, y, z} = {(a, x), (a, y), (a, z), (b, x), (b, y), (b, z)}
has cardinality 6. We now define the product of any number of cardinals.
Definition 3.2.3 — Let (Xi)i∈I be a family of sets. The Cartesian product Q
i∈I Xi
is defined as the set of families ( xi)i∈I such that xi ∈ Xi for all i ∈ I.
For a family (κi)i∈I of cardinals, their product Q
i∈I κi is defined as
Q
i∈I κi
. If
we only have two cardinals κ, λ, then we write their product as κ · λ = |κ × λ|.
Problem 3.2.2 (5 points)
Show that the Cartesian product Q
i∈I Xi is a set. Show that if Xi is nonempty for
all i ∈ I, then Q
i∈I Xi is nonempty.
Unfortunately, we have to deal with several abuses of notation here. Firstly, Q
i∈I κi is
used both for the Cartesian product of the cardinals and its cardinality.
Second, if we only have two sets X0, X1, then their Cartesian product as defined above,
call it X0 ⊗ X1 = Q
i∈2 Xi, is not equal to the Cartesian product X0 × X1 as defined in
Section 1! Thankfully, there is a natural bijection X0 ⊗ X1 → X0 × X1 sending (xi)i∈2
to (x0, x1), so there is nothing to worry about.
Problem 3.2.3 (10 points)
Show that
Q
i∈I Xi
 = Q
i∈I |Xi|. (The first Q is the Cartesian product of sets, and
the second Q is the product of cardinals.)
In particular, it follows that |X × Y | = |X| · |Y |. Just like cardinal addition, cardinal
multiplication satisfies many intuitive properties. It is associative: ( κ · λ) · µ = κ · (λ · µ),
commutative: κ · λ = λ · κ, distributive: κ · (λ + µ) = κ · λ + κ · µ, increasing: λ ≤ µ
implies κ · λ ≤ κ · µ, and finally, κ · 1 = κ and κ · 0 = 0. Furthermore, the sets F
i∈Y X
and X × Y are equal (not just equinumerous), so P
i∈I κ = κ · |I|.
Once again, it is important to stress that cardinal multiplication is not the same as
ordinal multiplication. For example, observe that the Cartesian product ω × 2 and the
ordinal ω · 2 are equinumerous: there is a bijection ω × 2 → ω · 2 which sends ( a, b) to
ω · b + a. It immediately follows that
ℵ0 · 2 = |ω × 2| = |ω · 2| = ℵ0.
Of course, ω · 2 = ω is not true under ordinal multiplication.
However, it turns out that for finite cardinals, cardinal arithmetic works exactly the
same way as ordinal arithmetic.
Problem 3.2.4 (10 points)
Prove that m +o n = m +c n and m ·o n = m ·c n for all natural numbers m, n∈ ω,
where +o, ·o denote ordinal addition and multiplication, and + c, ·c denote cardinal
addition and multiplication.
22
On the other hand, cardinal addition and multiplication are kind of trivial for infinite
cardinals, thanks to a theorem proven by Gerhard Hessenberg in 1906.
Theorem 3.2.4 (Hessenberg)
If κ is an infinite cardinal, then κ · κ = κ.
Proof. We have κ · κ ≥ κ · 1 = κ, so it suffices to show that κ · κ ≤ κ. Assume for the
sake of contradiction that κ · κ > κfor some infinite cardinal κ. Then, we may take κ to
be the smallest such cardinal.
We construct a well-order on κ × κ as follows:
(α1, β1) < (α2, β2) ⇐ ⇒max{α1, β1} < max{α2, β2}
∨ (max{α1, β1} = max{α2, β2} ∧α1 < α2)
∨ (max{α1, β1} = max{α2, β2} ∧α1 = α2 ∧ β1 < β2).
It is not hard to check that this is indeed a well-order. A visualization of this is shown
below, where ( α, β) is the cell on the αth row and the βth column.
...
· · ·
...
· · ·
...
· · ·
...
· · ·
...
· · ·
...
· · ·
...
· · ·
...
· · ·
...
· · ·
...
· · ·
...
· · ·
...
· · ·
0
0 0 1 4 9
1
1 2 3 5 10
2
2 6 7 8 11
3
3 12 13 14 15
ω
ω
ω
ω · 2 ω · 3
ω + 1
ω2 + 1
ω + 2
ω2 + 2
ω + 3
ω2 + 3
Let ξ be the order type of ( κ × κ, <). By assumption, we have ξ ≥ |κ × κ| = κ · κ > κ,
so suppose that the order-isomorphism ξ → κ × κ maps κ to (α, β). In other words, the
set X = {(α′, β′) ∈ κ × κ : (α′, β′) < (α, β)} has order type κ under <. Note that α and
β can’t both be finite, as otherwise X would be finite.
Next, let δ = S(max{α, β}), which is infinite but less than κ. Then X ⊆ δ × δ, so the
order type of ( δ × δ, <) is at least κ. In particular, |δ| · |δ| = |δ × δ| ≥κ >|δ|. However,
we had defined κ to be the smallest infinite cardinal such that κ · κ > κ. So since |δ| is
an infinite cardinal smaller than κ, we have a contradiction.
From this, we find that cardinal addition and multiplication with infinite cardinals is
given by a very simple formula:
Problem 3.2.5 (5 points)
Show that if κ and λ are nonzero cardinals and at least one of them is infinite, then
κ + λ = κ · λ = max{κ, λ}.
23
We also get a nice application to ordinal arithmetic.
Problem 3.2.6 (10 points)
Prove that if α and β are nonzero ordinals and at least one of them is infinite, then
|α + β| = |α · β| = max{|α|, |β|}.
Finally, we take a brief look at cardinal exponentiation.
Definition 3.2.5 — For two sets X, Y, the hom-set Hom(X, Y) (also denoted X Y
or sometimes Y X ) is the set of functions from X to Y .
For two cardinals κ, λ, define κλ = |Hom(λ, κ)|.
Note that Hom(X, Y) ⊆ P(X × Y ), so Hom(X, Y) is a set. Furthermore, it is easy to
show (similarly to Problems 3.2.1 and 3.2.3) that |Hom(X, Y)| = |Y ||X|.
Problem 3.2.7 (5 points)
Show that |P(X)| = 2|X| for any set X.
Just like before, we list some easy properties of cardinal exponentiation. It satisfies
the “distributive” identities ( κ · λ)µ = κµ · λµ and κλ+µ = κλ · κµ and κλ·µ = (κλ)µ, the
“unit” identities κ0 = 1 (in particular, 0 0 = 1) and 1 κ = 1 and 0 κ = 0 for κ >0, and is
increasing: κ ≤ λ implies κµ ≤ λµ, and 0 < λ≤ µ implies κλ ≤ κµ. Finally, observe that
the sets Q
i∈X Y and Hom(X, Y) are equal, so Q
i∈I κ = κ|I|.
Problem 3.2.8 (5 points)
Show that if 2 ≤ κ ≤ λ and λ is infinite, then κλ = 2λ.
Cardinal exponentiation is much more mysterious than addition or multiplication. For
finite cardinals, it is of course easy to compute, but for infinite cardinals, the very first
nontrivial computation already leaves us stumped: what is 2 ℵ0?
Definition 3.2.6 — The cardinality of the continuum is the cardinal c = 2ℵ0.
We know, from previous problems, that c = |P(ω)| = |R|. (The continuum refers to
the set R, which is “continuous”, hence the name.) So which aleph number is c equal to?
The continuum hypothesis (CH) states that c = ℵ1, a natural guess. But surprisingly, it
is impossible to prove or disprove the continuum hypothesis using the axioms of ZFC!
This strange phenomenon will be discussed shortly, and we will prove it by the end of
this Power Round.
What about even larger cases, such as 2 ℵ1? We can make the following guess:
2ℵα = ℵα+1 for all ordinals α.
This is known as the generalized continuum hypothesis (GCH). Of course, GCH implies
CH, but not the other way around. In particular, GCH is impossible to prove. In fact, it
is also impossible to disprove.
It turns out that if we assume the generalized continuum hypothesis, then cardinal
exponentiation becomes very nice, as we will see shortly.
24
3.3 Cofinality (60 points)
Suppose that c = ℵθ. Since c is uncountable, we have θ ≥ 1. Can we say anything else
about θ? Not much, as it turns out, but we can use the concept of cofinality to rule out
a few possibilities for θ. For instance, we will see that θ can’t equal ω.
Definition 3.3.1 — Let α be a limit ordinal. For an ordinal β, a function f : β → α
is cofinal if sup{f (γ) : γ < β} = α. The cofinality of α is the least ordinal cf α such
that there exists a cofinal function cf α → α.
An infinite cardinal κ is regular if cf κ = κ, and singular if cf κ < κ.
If α is a limit ordinal, then by Problem 2.2.1, the identity function id : α → α (where
id(β) = β for β < α) is cofinal, so the cofinality cf α is well-defined and at most α. (If α
is a successor ordinal, then no function β → α is cofinal.)
Intuitively, the cofinality of α measures how easy it is to approach α. For example, the
cardinal ℵω1+ω is quite large, but it is very easy to approach. The function ω → ℵω1+ω
sending n to ℵω1+n is cofinal, so cf ℵω1+ω ≤ ℵ0. That is, we can approach ℵω1+ω using
ℵ0 ordinals. By Problem 3.3.1 below, the cofinality can’t be finite, so cf ℵω1+ω = ℵ0.
On the other hand, the cardinal ℵω+1 is much smaller, but it is much more difficult
to approach. In fact, by Problem 3.3.2 below, it is regular: cf ℵω+1 = ℵω+1, so we need
ℵω+1 ordinals to approach ℵω+1.
Problem 3.3.1 (15 points)
Prove that cf α is always a regular cardinal.
Problem 3.3.2 (10 points)
Let α be an ordinal. Prove that
(a) If α = 0 or α = β + 1, then ℵα is regular.
(b) If α is a limit ordinal, then cf ℵα = cf α.
In order to apply the concept of cofinality to study c, we need K¨ onig’s theorem, first
shown by Gyula K¨ onig in 1905.
Problem 3.3.3 (15 points)
Let (κi)i∈I and (λi)i∈I be families of cardinals such that κi < λi for all i ∈ I. Then
X
i∈I
κi <
Y
i∈I
λi.
(Hint: if κi = 1 and λi = 2 for all i ∈ I, then we get |I| < 2|I|, so K¨ onig’s theorem
generalizes Cantor’s theorem. Does the proof generalize as well?)
Problem 3.3.4 (10 points)
Prove that if κ is an infinite cardinal, then cf 2 κ > κ.
25
In particular, this means that cf c > ℵ0. So if c = ℵθ, then θ must either be a successor
ordinal, or a limit ordinal with cofinality > ℵ0. This rules out a few possibilities for what
θ can be: for instance, θ can’t equal ω, or ω · 2, or ω1 + ω, or ωω, and so on.
We end with another application to cardinal exponentiation. For an infinite cardinal
κ, let κ+ denote the smallest cardinal greater than κ (that is, ℵ+
α = ℵα+1).
Problem 3.3.5 (10 points)
Assuming the generalized continuum hypothesis, prove that if κ and λ are infinite
cardinals such that cf κ > λ, then κλ = κ.
Theorem 3.3.2
Under the generalized continuum hypothesis, if κ and λ are infinite cardinals, then
(a) If λ <cf κ, then κλ = κ.
(b) If cf κ ≤ λ < κ, then κλ = κ+.
(c) If λ ≥ κ, then κλ = λ+.
Proof. (a) is Problem 3.3.5, and (c) follows from Problem 3.2.8: if λ ≥ κ, then by GCH,
we have κλ = 2λ = λ+. From now on, we assume that cf κ ≤ λ < κ.
It suffices to show that κcf κ > κ. Indeed, if this is true, then we have κλ ≤ κκ = κ+
and κλ ≥ κcf κ ≥ κ+, so κλ = κ+, and we would be done.
Let s : cf κ → κ be cofinal, and for the sake of contradiction, suppose that κcf κ ≤ κ,
so that there exists a surjective function F : κ → Hom(cf κ, κ). Next, define a function
f : cf κ → κ as follows: for ξ <cf κ, define f (ξ) as the smallest ordinal γ < κsuch that
γ ̸= (F (α))(ξ) for any α < s(ξ). (Such a γ always exists, as |s(ξ)| < κ.)
Since F is surjective, we have f = F (α) for some α. However, since s is cofinal, there
exists some ξ such that s(ξ) > α. Hence, f (ξ) ̸= (F (α))(ξ), a contradiction.
3.4 Interlude: G¨ odel’s Incompleteness Theorems
In September 1930, David Hilbert gave a fiery speech for his retirement address at the
K¨ onigsberg conference, ending with the words “Wir m¨ ussen wissen. Wir werden wissen!”
(Translation: “We must know. We shall know!”) These words were later engraved on his
tombstone.
Hilbert believed that mathematics was complete: that it was possible to find a set of
axioms for the entirety of mathematics, such that every statement can be either proved
or disproved from the axioms. Of course, he also wanted to make sure that those axioms
were consistent: that it was impossible to prove an obviously false statement.
But at the very same conference, a young Kurt G¨ odel announced his newest result: in
any4 consistent system of axioms, there will always statements that are neither provable
nor disprovable – they are independent from the axioms. This is known as G¨ odel’s first
incompleteness theorem. Shortly thereafter, G¨ odel published this result, and with that,
Hilbert’s dream shattered.
We give a brief exposition of G¨ odel’s work below.
4Actually, there are some additional technical conditions required: the set of axioms must be recursively
enumerable, and the theory must be capable of describing the addition and multiplication of natural
numbers. But all you need to know is that ZFC satisfies these conditions.
26
Definition 3.4.1 — Let φ be a sentence. We write ZFC ⊢ φ if we can prove φ in
ZFC. If ZFC ⊬ φ and ZFC ⊬ ¬φ, then we say that φ is independent from ZFC.
Let ⊥ denote the sentence ∃x (x ̸= x), which is clearly false. We say that ZFC is
consistent if ZFC ⊬ ⊥.
Theorem 3.4.2 (G¨ odel, Rosser)
If ZFC is consistent, then there exists a sentence which is independent from ZFC.
The condition that ZFC is consistent is necessary. If we could prove a false sentence
in ZFC, then we would be able to prove every possible sentence, and nothing would be
independent (and mathematics would fall apart).
The construction that G¨ odel gave, theG¨ odel sentence, works by creating some clever
interplay between the base theory and the coded theory. First, we construct a formula
Bew(⌜φ⌝), which states that ⌜φ⌝ can be proved in the coded theory ⌜ZFC⌝. (The name
of the formula is short for Beweis, which is German for “proof”.) The formula satisfies
the following provability conditions:
1. If ZFC ⊢ φ, then ZFC ⊢ Bew(⌜φ⌝).
2. ZFC proves Bew(⌜φ⌝) =⇒ Bew(⌜Bew(⌜φ⌝)⌝).
3. ZFC proves (Bew(⌜φ⌝) ∧ Bew(⌜φ ⇒ ψ⌝)) =⇒ Bew(⌜ψ⌝).
The G¨ odel sentenceG is then constructed, using a clever trick, so that ZFC pr
...[truncated]
