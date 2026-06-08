# Results: openai/gpt-5.5

## econ_ieo_2019_q1 — Mechanism Design (2019)
**Score: 30/30 / 30**

### Agent Answer

## a) Alice’s cut in the simple mechanism

Let the three pieces Alice cuts have sizes

\[
x_1\le x_2\le x_3,\qquad x_1+x_2+x_3=1.
\]

Bob moves first and wants as much cake as possible, so he takes the largest piece, size \(x_3\). Clara then takes the largest of the two remaining pieces, size \(x_2\). Therefore Alice is left with the smallest piece, size \(x_1\).

So Alice wants to maximize the size of the smallest piece. But since

\[
3x_1 \le x_1+x_2+x_3=1,
\]

we must have

\[
x_1\le \frac13.
\]

Alice can achieve \(x_1=1/3\) by cutting the cake into three equal pieces.

Therefore Alice cuts the cake into three equal pieces of size

\[
\boxed{\frac13,\frac13,\frac13}.
\]

Then Bob, Clara, and Alice each get \(1/3\).

---

## b) Threshold preferences

Alice needs at least \(a\), Bob at least \(b\), Clara at least \(c\), where

\[
0<a,b,c<1.
\]

A child is happy iff he or she receives at least the required amount.

### Necessity

If there is any mechanism that guarantees all three children are happy, then in the final allocation the shares \(x_A,x_B,x_C\) must satisfy

\[
x_A\ge a,\qquad x_B\ge b,\qquad x_C\ge c.
\]

Since the whole cake has size \(1\),

\[
x_A+x_B+x_C\le 1.
\]

Therefore necessarily,

\[
a+b+c\le x_A+x_B+x_C\le 1.
\]

So a necessary condition is

\[
\boxed{a+b+c\le 1}.
\]

If \(a+b+c>1\), then there is not enough cake to give everyone their minimum acceptable amount, so no mechanism can make everyone happy.

---

### Sufficiency: a mechanism when \(a+b+c\le 1\)

Suppose

\[
a+b+c\le 1.
\]

Use the following mechanism.

1. Alice proposes a division of the cake into three labeled pieces: one for Alice, one for Bob, one for Clara.
2. Bob and Clara observe their proposed pieces.
3. Bob and Clara each say “accept” or “reject.”
4. If both accept, the proposed division is implemented.
5. If either rejects, nobody gets any cake.

Now solve this mechanism by backward induction.

Bob will accept exactly when his proposed piece is at least \(b\), because getting at least \(b\) is better than getting no cake, while getting a positive amount less than \(b\) is worse than getting no cake.

Similarly, Clara will accept exactly when her proposed piece is at least \(c\).

Alice knows \(b\) and \(c\). Therefore, if she wants her proposal to be accepted, she must give Bob at least \(b\) and Clara at least \(c\). Since Alice wants as much cake as possible, she gives them exactly their minimum acceptable amounts:

\[
x_B=b,\qquad x_C=c.
\]

Then Alice keeps the remaining cake:

\[
x_A=1-b-c.
\]

Because we assumed

\[
a+b+c\le 1,
\]

we have

\[
1-b-c\ge a.
\]

Thus Alice also gets at least her required amount.

So the final allocation is

\[
\boxed{x_A=1-b-c,\qquad x_B=b,\qquad x_C=c.}
\]

Everyone is happy.

Therefore a mechanism ensuring that all three children are happy exists exactly when

\[
\boxed{a+b+c\le 1}.
\]

### Judge Feedback

a) **10/10 rp**

- The student correctly identifies that Bob will take the largest piece and Clara will take the largest remaining piece, leaving Alice with the smallest piece.
- The student correctly argues that Alice maximizes the smallest piece by making all three pieces equal.
- Correct conclusion: Alice cuts the cake into three pieces of size \(1/3,1/3,1/3\).

**Score for a): 10/10**

---

b) **20/20 rp**

- The student gives the correct necessary condition:

\[
a+b+c\le 1.
\]

- The necessity is correctly explained: if \(a+b+c>1\), there is not enough cake to give all three children their minimum acceptable shares.
- The proposed mechanism is correct:
  1. Alice proposes a full labeled allocation.
  2. Bob and Clara vote accept/reject.
  3. If both accept, the allocation is implemented.
  4. If either rejects, nobody gets cake.

- The mechanism satisfies both crucial features from the rubric:
  1. The distribution is proposed by one of the children, Alice, who knows \(a,b,c\).
  2. If the proposed distribution does not satisfy Bob or Clara’s requirements, they can reject and everyone gets nothing.

- The explanation of why the mechanism works is complete:
  - Bob accepts iff he gets at least \(b\).
  - Clara accepts iff she gets at least \(c\).
  - Alice therefore gives Bob \(b\), Clara \(c\), and keeps \(1-b-c\).
  - Since \(a+b+c\le 1\), Alice gets at least \(a\).
  - Hence everyone is happy.

**Score for b): 20/20**

---

TOTAL: 30/30

---

## econ_ieo_2021_q1 — Dynamic Equilibrium (2021)
**Score: 30/30 / 30**

### Agent Answer

## (a) Static equilibrium when \(K=210\)

Equilibrium requires demand = supply in both markets.

### Oil \(A\)

\[
D_A=S_A
\]

\[
K-2P_A+P_B=-10+2P_A
\]

With \(K=210\):

\[
210-2P_A+P_B=-10+2P_A
\]

\[
4P_A-P_B=220
\]

### Gas \(B\)

\[
D_B=S_B
\]

\[
80-6P_B+2P_A=-5+P_B
\]

\[
7P_B-2P_A=85
\]

So we solve

\[
4P_A-P_B=220
\]

\[
7P_B-2P_A=85
\]

From the first equation,

\[
P_B=4P_A-220
\]

Substitute into the second:

\[
7(4P_A-220)-2P_A=85
\]

\[
28P_A-1540-2P_A=85
\]

\[
26P_A=1625
\]

\[
P_A^*=62.5
\]

Then

\[
P_B^*=4(62.5)-220=30
\]

So the equilibrium prices are

\[
\boxed{P_A^*=62.5,\qquad P_B^*=30}
\]

Equilibrium quantities:

\[
Q_A^*=S_A=-10+2(62.5)=115
\]

\[
Q_B^*=S_B=-5+30=25
\]

Thus

\[
\boxed{Q_A^*=115,\qquad Q_B^*=25}
\]

---

## (b) Production decisions for period 2 when firms expect \(K_2=80\)

Firms choose production one period in advance. In period 1, they expect \(K_2=80\), so they base production for period 2 on the expected equilibrium with \(K=80\).

Equilibrium equations become:

### Oil

\[
80-2P_A+P_B=-10+2P_A
\]

\[
4P_A-P_B=90
\]

### Gas

Gas demand is unchanged:

\[
80-6P_B+2P_A=-5+P_B
\]

\[
7P_B-2P_A=85
\]

Solve:

\[
P_B=4P_A-90
\]

Substitute:

\[
7(4P_A-90)-2P_A=85
\]

\[
28P_A-630-2P_A=85
\]

\[
26P_A=715
\]

\[
P_A^e=27.5
\]

Then

\[
P_B^e=4(27.5)-90=20
\]

So expected prices are

\[
P_A^e=27.5,\qquad P_B^e=20
\]

Production for period 2 is based on supply at these expected prices:

\[
Q_A^2=S_A=-10+2(27.5)=45
\]

\[
Q_B^2=S_B=-5+20=15
\]

Therefore the quantities produced for sale in period 2 are

\[
\boxed{Q_A^2=45,\qquad Q_B^2=15}
\]

---

## (c) Actual period-2 prices when \(K_2=210\)

The prediction was wrong. Actual demand is based on \(K_2=210\), but production is fixed at

\[
Q_A^2=45,\qquad Q_B^2=15
\]

Prices must clear the market:

### Oil

\[
D_A=45
\]

\[
210-2P_A+P_B=45
\]

\[
2P_A-P_B=165
\]

### Gas

\[
D_B=15
\]

\[
80-6P_B+2P_A=15
\]

\[
2P_A-6P_B=-65
\]

Now solve:

\[
2P_A-P_B=165
\]

\[
2P_A-6P_B=-65
\]

Subtract the first equation from the second:

\[
-5P_B=-230
\]

\[
P_B=46
\]

Then

\[
2P_A-46=165
\]

\[
2P_A=211
\]

\[
P_A=105.5
\]

So the period-2 market-clearing prices are

\[
\boxed{P_A^2=105.5,\qquad P_B^2=46}
\]

The mistaken expectation caused underproduction, so prices rise sharply.

---

## (d) Naive expectations from period 2 onward

From period 2 onward, firms expect next period’s prices to equal current prices:

\[
P_{A,t+1}^e=P_{A,t},\qquad P_{B,t+1}^e=P_{B,t}
\]

Therefore production for period \(t+1\) is

\[
Q_{A,t+1}=-10+2P_{A,t}
\]

\[
Q_{B,t+1}=-5+P_{B,t}
\]

Actual demand always has \(K=210\). Thus prices in period \(t+1\) must satisfy:

\[
210-2P_{A,t+1}+P_{B,t+1}=Q_{A,t+1}
\]

\[
80-6P_{B,t+1}+2P_{A,t+1}=Q_{B,t+1}
\]

Substitute production:

\[
210-2P_{A,t+1}+P_{B,t+1}=-10+2P_{A,t}
\]

\[
80-6P_{B,t+1}+2P_{A,t+1}=-5+P_{B,t}
\]

Rearranging:

\[
2P_{A,t+1}-P_{B,t+1}=220-2P_{A,t}
\]

\[
2P_{A,t+1}-6P_{B,t+1}=P_{B,t}-85
\]

Solving this system gives the dynamic price equations:

\[
P_{A,t+1}=140.5-1.2P_{A,t}-0.1P_{B,t}
\]

\[
P_{B,t+1}=61-0.4P_{A,t}-0.2P_{B,t}
\]

The fixed point of this system is the original static equilibrium:

\[
\bar P_A=62.5,\qquad \bar P_B=30
\]

with outputs

\[
\bar Q_A=115,\qquad \bar Q_B=25
\]

However, we need to check whether this fixed point is stable.

Write deviations from equilibrium as

\[
x_t=P_{A,t}-62.5,\qquad y_t=P_{B,t}-30
\]

Then

\[
\begin{pmatrix}
x_{t+1}\\
y_{t+1}
\end{pmatrix}
=
\begin{pmatrix}
-1.2 & -0.1\\
-0.4 & -0.2
\end{pmatrix}
\begin{pmatrix}
x_t\\
y_t
\end{pmatrix}
\]

The eigenvalues of the matrix are found from

\[
\lambda^2+1.4\lambda+0.2=0
\]

\[
\lambda=\frac{-1.4\pm \sqrt{1.16}}{2}
\]

So

\[
\lambda_1\approx -0.1615
\]

\[
\lambda_2\approx -1.2385
\]

Because one eigenvalue has absolute value greater than 1,

\[
|\lambda_2|>1
\]

the system is unstable. Therefore prices do not converge to the equilibrium. Instead, they oscillate around the equilibrium with increasing amplitude.

Starting from the period-2 prices found in part (c),

\[
P_{A,2}=105.5,\qquad P_{B,2}=46
\]

we can see the oscillation:

\[
Q_{A,3}=-10+2(105.5)=201
\]

\[
Q_{B,3}=-5+46=41
\]

These large quantities then cause prices in period 3 to fall:

\[
P_{A,3}=9.3,\qquad P_{B,3}=9.6
\]

Then production for period 4 is low:

\[
Q_{A,4}=-10+2(9.3)=8.6
\]

\[
Q_{B,4}=-5+9.6=4.6
\]

This causes prices to rise again:

\[
P_{A,4}=128.38,\qquad P_{B,4}=55.36
\]

Thus the economy experiences explosive cobweb-type cycles.

Therefore, as \(t\to\infty\),

\[
\boxed{\text{prices do not converge}}
\]

and

\[
\boxed{\text{outputs do not converge}}
\]

Instead, in the unconstrained linear model, both prices and outputs oscillate with increasing amplitude. Mathematically, the dynamics are unstable. Economically, the model eventually gives unrealistic negative outputs or prices, showing that the linear model breaks down far from equilibrium.

### Judge Feedback

(a) **5/5 rp**  
The student correctly sets demand equal to supply in both markets for \(K=210\), solves the system, and obtains:
\[
P_A^*=62.5,\qquad P_B^*=30
\]
Both equilibrium prices are correct. Extra equilibrium quantities are also correct, though not required.

(b) **10/10 rp**  
The student correctly computes the expected equilibrium when firms expect \(K_2=80\):
\[
P_A^e=27.5,\qquad P_B^e=20
\]
Then correctly uses the supply functions to determine production for period 2:
\[
Q_A^2=45,\qquad Q_B^2=15
\]
Both quantities are correct.

(c) **5/5 rp**  
The student correctly treats production as fixed at:
\[
Q_A=45,\qquad Q_B=15
\]
and clears the market with actual \(K_2=210\), obtaining:
\[
P_A^2=105.5,\qquad P_B^2=46
\]
Both prices are correct.

(d) **10/10 rp**  
The student gives a clear dynamic analysis under naive expectations, derives the correct transition equations:
\[
P_{A,t+1}=140.5-1.2P_{A,t}-0.1P_{B,t}
\]
\[
P_{B,t+1}=61-0.4P_{A,t}-0.2P_{B,t}
\]
They correctly identify the fixed point as the static equilibrium and show instability using eigenvalues, with one eigenvalue having absolute value greater than 1. They also provide numerical examples matching the sample solution and conclude that prices and outputs oscillate with increasing amplitude. This fully satisfies the rubric’s requirement for increasing fluctuations with numeric proof.

TOTAL: 30/30

---

## econ_ieo_2022_q5 — Going Green (Bandwagon Effect) (2022)
**Score: 30/30 / 30**

### Agent Answer

We need be careful about one point: a group cannot demand a negative number of panels. So I will interpret the given demand formula as giving raw demand, with actual demand truncated at zero if the formula is negative. The upper bounds of 150,000 and 200,000 households do not bind in the equilibria below.

Let the effective consumer price be \(p\).

---

## (a) No subsidy

Supply is perfectly elastic at

\[
p=25{,}000.
\]

Environmental consumers buy first:

\[
Q_c=150{,}000-5(25{,}000)=150{,}000-125{,}000=25{,}000.
\]

So initially

\[
N=25{,}000.
\]

Now the trendy consumers observe \(N=25{,}000\). Their raw demand is

\[
Q_b=40{,}000-5(25{,}000)+500\sqrt{25{,}000}.
\]

Since \(\sqrt{25{,}000}\approx 158.11\),

\[
Q_b=40{,}000-125{,}000+500(158.11)
\]

\[
Q_b=-85{,}000+79{,}056\approx -5{,}944<0.
\]

So actual trendy demand is zero. Therefore no trendy consumers buy, and the process stops.

\[
\boxed{N=25{,}000}
\]

So 25,000 solar panels are purchased.

There are other self-consistent bandwagon equilibria at this price, but they are not reached from the described starting point because the initial environmental adoption is too small to start the bandwagon process.

---

## (b) Subsidy of \(s=\$5{,}000\)

With a per-unit subsidy of \$5,000, the effective consumer price falls to

\[
p=25{,}000-5{,}000=20{,}000.
\]

Environmental demand becomes

\[
Q_c=150{,}000-5(20{,}000)=150{,}000-100{,}000=50{,}000.
\]

So initially,

\[
N=50{,}000.
\]

At price \(20{,}000\), trendy demand is

\[
Q_b=40{,}000-5(20{,}000)+500\sqrt{N}
\]

\[
Q_b=40{,}000-100{,}000+500\sqrt{N}
\]

\[
Q_b=-60{,}000+500\sqrt{N}.
\]

In equilibrium,

\[
N=Q_c+Q_b.
\]

Thus

\[
N=50{,}000+\left(-60{,}000+500\sqrt{N}\right)
\]

\[
N=-10{,}000+500\sqrt{N}.
\]

Let

\[
x=\sqrt{N}.
\]

Then \(N=x^2\), so

\[
x^2=-10{,}000+500x.
\]

Rearranging,

\[
x^2-500x+10{,}000=0.
\]

Using the quadratic formula,

\[
x=\frac{500\pm \sqrt{500^2-4(10{,}000)}}{2}
\]

\[
x=\frac{500\pm \sqrt{250{,}000-40{,}000}}{2}
\]

\[
x=\frac{500\pm \sqrt{210{,}000}}{2}.
\]

Since \(\sqrt{210{,}000}=100\sqrt{21}\),

\[
x=250\pm 50\sqrt{21}.
\]

The smaller root gives \(N<50{,}000\), which is impossible because environmental consumers alone buy 50,000 panels. So we take the larger root:

\[
x=250+50\sqrt{21}.
\]

Therefore

\[
N=(250+50\sqrt{21})^2.
\]

Expanding,

\[
N=115{,}000+25{,}000\sqrt{21}.
\]

Numerically,

\[
\sqrt{21}\approx 4.5826,
\]

so

\[
N\approx 115{,}000+25{,}000(4.5826)
\]

\[
N\approx 229{,}564.
\]

Thus the equilibrium quantity with the subsidy is

\[
\boxed{N\approx 229{,}564}
\]

solar panels.

The trendy-group quantity is

\[
Q_b=N-Q_c\approx 229{,}564-50{,}000=179{,}564,
\]

which is below the group size of 200,000, so the group-size constraint does not bind.

---

## (c) Subsidy eliminated after the high-subsidy equilibrium is reached

After the subsidy is removed, the consumer price returns to

\[
p=25{,}000.
\]

At this price, environmental demand again becomes

\[
Q_c=150{,}000-5(25{,}000)=25{,}000.
\]

For trendy consumers,

\[
Q_b=40{,}000-5(25{,}000)+500\sqrt{N}
\]

\[
Q_b=-85{,}000+500\sqrt{N}.
\]

In a bandwagon equilibrium after the subsidy is removed,

\[
N=Q_c+Q_b.
\]

So

\[
N=25{,}000+\left(-85{,}000+500\sqrt{N}\right)
\]

\[
N=-60{,}000+500\sqrt{N}.
\]

Let \(x=\sqrt{N}\). Then

\[
x^2=-60{,}000+500x,
\]

so

\[
x^2-500x+60{,}000=0.
\]

Using the quadratic formula,

\[
x=\frac{500\pm \sqrt{500^2-4(60{,}000)}}{2}
\]

\[
x=\frac{500\pm \sqrt{250{,}000-240{,}000}}{2}
\]

\[
x=\frac{500\pm 100}{2}.
\]

Thus

\[
x=200 \quad \text{or} \quad x=300.
\]

So the corresponding quantities are

\[
N=200^2=40{,}000
\]

or

\[
N=300^2=90{,}000.
\]

There is also the no-bandwagon equilibrium \(N=25{,}000\), as in part (a). But now the economy is not starting from 25,000 panels. It is starting from the subsidy equilibrium,

\[
N\approx 229{,}564.
\]

Because this is well above the unstable tipping point of 40,000, the market converges to the high no-subsidy equilibrium:

\[
\boxed{N=90{,}000}.
\]

At that equilibrium,

\[
Q_c=25{,}000,
\]

and

\[
Q_b=90{,}000-25{,}000=65{,}000.
\]

Check:

\[
Q_b=-85{,}000+500\sqrt{90{,}000}
\]

\[
=-85{,}000+500(300)
\]

\[
=-85{,}000+150{,}000=65{,}000.
\]

So the equilibrium is consistent.

Therefore after the subsidy is removed, the new equilibrium quantity of installed solar panels is

\[
\boxed{90{,}000}.
\]

This is not the same as in part (a), where the quantity was only 25,000. The reason is path dependence caused by the bandwagon effect. Without the subsidy, the market starts with only 25,000 environmentally motivated users, which is too small to trigger trendy consumers to buy. But the temporary subsidy pushes adoption above the critical mass. Once many people have panels, enough trendy consumers still want them even after the subsidy is removed, so the market remains at a higher equilibrium.

### Judge Feedback

Criterion 1: Check whether \(Q_b\) is positive before applying the bandwagon equilibrium condition — **6/6**

The student correctly notes that demand cannot be negative and explicitly checks that at \(p=25{,}000\), starting from \(Q_c=25{,}000\), the raw bandwagon demand is negative, so no bandwagon adoption occurs in part (a). They also correctly proceed with the equilibrium condition in parts (b) and (c), where bandwagon demand is positive at the relevant equilibria.

Criterion 2: Specify the equilibrium condition with parameters plugged in — **10/10**

The student correctly writes the equilibrium conditions:

- Part (b):  
\[
N=50{,}000-60{,}000+500\sqrt N
\]
leading to  
\[
x^2-500x+10{,}000=0.
\]

- Part (c):  
\[
N=25{,}000-85{,}000+500\sqrt N
\]
leading to  
\[
x^2-500x+60{,}000=0.
\]

They also correctly explain why the equilibrium equation is not reached in part (a) from the initial condition.

Criterion 3: Solve for equilibrium values of \(N\) — **6/6**

The student obtains all three correct quantities:

- Part (a): \(N=25{,}000\)
- Part (b): \(N\approx 229{,}564\)
- Part (c): \(N=90{,}000\)

Full credit.

Criterion 4: Account for the 200,000-person upper bound for the bandwagon group — **3/3**

The student explicitly states that the household upper bounds do not bind and checks in part (b) that

\[
Q_b\approx 179{,}564<200{,}000.
\]

In parts (a) and (c), the bandwagon quantities are also below 200,000. Full credit.

Criterion 5: Explain whether part (c) is the same as part (a) and why — **5/5**

The official sample solution says the answer in part (c) is **not** the same as in part (a), because the temporary subsidy moves the market past the critical mass needed for the bandwagon effect. The student gives exactly this explanation: the market is path-dependent, and after subsidy removal it converges to the high no-subsidy equilibrium \(N=90{,}000\), not back to \(25{,}000\).

The rubric line saying “the result in (c) is the same as in (a)” appears to contradict the official solution, so I grade this according to the official solution.

TOTAL: 30/30

---

## econ_ieo_2020_q2 — Optimal Lockdown (2020)
**Score: 28/30 / 30**

### Agent Answer

## (a) Individual decisions: Nash equilibrium

Let \(n\) be the total number of people who go outside.

If person \(i\) goes outside, then the number of other people outside is \(n-1\), so her utility is

\[
U_i^{out}=50-\frac{n-1}{200}i.
\]

If person \(i\) stays home, her utility is \(0\). If she deviates and goes outside while the other \(n\) people remain outside, her utility would be

\[
50-\frac{n}{200}i.
\]

For a Nash equilibrium:

1. Everyone who goes outside must weakly prefer going outside:

\[
50-\frac{n-1}{200}i \ge 0
\]

\[
i \le \frac{10000}{n-1}.
\]

2. Everyone who stays home must weakly prefer staying home:

\[
50-\frac{n}{200}i \le 0
\]

\[
i \ge \frac{10000}{n}.
\]

So low-risk people, those with small \(i\), are the ones who go outside.

Now check possible \(n\).

### Rule out \(n \le 99\)

If \(n=99\), then a person staying home would want to go outside if

\[
50-\frac{99}{200}i>0
\]

\[
i<\frac{10000}{99}\approx 101.01.
\]

So citizens \(1,\dots,101\) would strictly want to go outside. That is already 101 people, contradicting \(n=99\).

For any \(n<99\), even more people would want to go outside. Therefore

\[
n \le 99
\]

cannot be a Nash equilibrium.

### Rule out \(n \ge 101\)

If \(n\ge 101\), then someone going outside must satisfy

\[
i \le \frac{10000}{n-1}.
\]

For \(n=101\),

\[
\frac{10000}{100}=100.
\]

So only citizens \(1,\dots,100\) would be willing to go outside, but we need 101 people outside. Impossible.

For larger \(n\), the threshold is even lower. Therefore

\[
n \ge 101
\]

cannot be a Nash equilibrium.

Thus the only possible number is

\[
n=100.
\]

Check that \(n=100\) works.

If 100 people are outside, then an outsider faces \(Q=99\), so

\[
U_i=50-\frac{99}{200}i.
\]

This is nonnegative for

\[
i \le \frac{10000}{99}\approx 101.01.
\]

A person staying home faces \(Q=100\) if she deviates, so she would get

\[
50-\frac{100}{200}i=50-\frac{i}{2}.
\]

This is nonpositive for

\[
i\ge 100.
\]

So a Nash equilibrium is: citizens \(1,\dots,99\) go outside, and then either citizen 100 or citizen 101 also goes outside. Everyone else stays home.

Therefore,

\[
\boxed{N=100.}
\]

---

## (b) Social planner’s choice

Now the town administration chooses who may go outside in order to maximize total expected utility.

Suppose the administration allows \(k\) people outside. For any fixed \(k\), the risk for each person outside is based on \(Q=k-1\). The utility of citizen \(i\) if outside is

\[
50-\frac{k-1}{200}i.
\]

To maximize total welfare for a given \(k\), the administration should choose the \(k\) people with the lowest illness costs, namely citizens

\[
1,2,\dots,k.
\]

The total welfare from allowing citizens \(1,\dots,k\) outside is

\[
W(k)=\sum_{i=1}^k \left(50-\frac{k-1}{200}i\right).
\]

So

\[
W(k)=50k-\frac{k-1}{200}\sum_{i=1}^k i.
\]

Using

\[
\sum_{i=1}^k i=\frac{k(k+1)}{2},
\]

we get

\[
W(k)=50k-\frac{k-1}{200}\cdot \frac{k(k+1)}{2}.
\]

Thus

\[
W(k)=50k-\frac{k(k-1)(k+1)}{400}.
\]

Equivalently,

\[
W(k)=50k-\frac{k^3-k}{400}.
\]

We need to choose integer \(k\in\{0,1,\dots,200\}\) to maximize this.

Consider the marginal change from increasing \(k\) to \(k+1\):

\[
W(k+1)-W(k)
=50-\frac{(k+1)^3-(k+1)-(k^3-k)}{400}.
\]

Now,

\[
(k+1)^3-(k+1)-(k^3-k)=3k^2+3k.
\]

So

\[
W(k+1)-W(k)=50-\frac{3k(k+1)}{400}.
\]

The administration should keep adding people as long as this is positive:

\[
50-\frac{3k(k+1)}{400}>0.
\]

That is,

\[
50>\frac{3k(k+1)}{400}
\]

\[
20000>3k(k+1)
\]

\[
k(k+1)<\frac{20000}{3}\approx 6666.67.
\]

Now check nearby integers.

For \(k=81\),

\[
81\cdot 82=6642<6666.67,
\]

so

\[
W(82)>W(81).
\]

For \(k=82\),

\[
82\cdot 83=6806>6666.67,
\]

so

\[
W(83)<W(82).
\]

Therefore the welfare-maximizing number is

\[
\boxed{K=82.}
\]

The administration should allow citizens \(1,\dots,82\) to go outside.

---

## (c) Comparison and intuition

We found:

\[
\boxed{N=100}
\]

and

\[
\boxed{K=82.}
\]

So

\[
\boxed{N>K.}
\]

In the Nash equilibrium, too many people go outside compared with the social optimum.

The intuition is that when a person decides whether to go outside, she considers only her own benefit and her own infection risk. She does not take into account that by going outside she increases the infection probability for everyone else outside.

So each additional person outside creates a negative externality on others. Individually, people ignore this external cost. As a result, decentralized individual decision-making leads to excessive outside activity and too much disease risk.

This model illustrates the fundamental economic problem of:

\[
\boxed{\text{negative externalities / market failure}.}
\]

In particular, it is an infection externality: individual choices impose costs on others, so the private equilibrium is not socially efficient.

### Judge Feedback

(a) **12/12 points**

- **2/2** for identifying that the people with the lowest illness costs, i.e. lowest \(i\), will go outside.
- **8/8** for writing the correct Nash equilibrium incentive conditions:
  - Those outside must prefer going outside given \(n-1\) others outside.
  - Those staying home must not want to deviate given \(n\) others outside.
- **2/2** for correctly solving the integer conditions and obtaining  
  \[
  N=100.
  \]
  The student also correctly notes the possible equilibrium composition involving citizens \(1,\dots,99\) plus either citizen 100 or 101.

(b) **12/12 points**

- **2/2** for correctly stating that the planner should allow the citizens with the lowest illness costs to go outside.
- **8/8** for writing the correct social welfare objective:
  \[
  W(k)=50k-\frac{k(k-1)(k+1)}{400},
  \]
  and using the correct marginal welfare condition.
- **2/2** for correctly solving the integer optimization problem and obtaining  
  \[
  K=82.
  \]

(c) **4/6 points**

- **4/4** for correctly explaining the negative externality: each person going outside increases infection risk for others but does not internalize this cost.
- **0/2** for the fundamental economic problem: the student mentions “negative externalities / market failure,” which is correct intuition, but does not specifically mention under-provision of a public good or tragedy of the commons as required by the rubric.

TOTAL: 28/30

---

## econ_ieo_2025_q1 — Buying Cars (2025)
**Score: 30/30 / 30**

### Agent Answer

## (a) Narrative consistent with the payoff matrix

Let the first number in each cell be Lee’s payoff and the second be Xi’s payoff.

A consistent story is a **status competition** or “keeping up with the neighbors” story.

Suppose:

- A **modest car** is cheaper and practical, so its basic material payoff is high: say **2**.
- A **luxury car** is nicer, but much more expensive, so ignoring status its net material payoff is lower: say **1**.
- However, there is a **positional/status effect**:
  - If one family has a luxury car while the other has a modest car, the luxury-car family feels superior and receives a status bonus of **+1.5**.
  - The modest-car family feels inferior and receives a status penalty of **−1.5**.
  - If both families choose the same type of car, there is no relative status gain or loss.

Then the payoffs are:

1. **Both buy modest cars**:  
   Neither family feels inferior, and both save money.  
   Payoffs:  
   \[
   (2,2)
   \]

2. **Lee buys modest, Xi buys luxury**:  
   Lee saves money but feels inferior:  
   \[
   2-1.5=0.5
   \]  
   Xi bears the cost of luxury but gets status:  
   \[
   1+1.5=2.5
   \]  
   Payoffs:  
   \[
   (0.5,2.5)
   \]

3. **Lee buys luxury, Xi buys modest**:  
   Symmetrically, Lee gets the status advantage and Xi feels inferior.  
   Payoffs:  
   \[
   (2.5,0.5)
   \]

4. **Both buy luxury cars**:  
   Both pay the high cost of luxury cars, but since both have luxury cars, neither gains relative status.  
   Payoffs:  
   \[
   (1,1)
   \]

So the payoff matrix represents a situation where luxury cars are individually attractive because of status competition, but collectively wasteful because if everyone buys luxury cars, the status advantage disappears.

---

## (b) Nash equilibrium and social desirability

The payoff matrix is:

\[
\begin{array}{c|cc}
 & \text{Xi Modest} & \text{Xi Luxury} \\
\hline
\text{Lee Modest} & (2,2) & (0.5,2.5) \\
\text{Lee Luxury} & (2.5,0.5) & (1,1)
\end{array}
\]

Consider Lee’s best responses.

- If Xi chooses **Modest**, Lee gets:
  \[
  2 \text{ from Modest}, \quad 2.5 \text{ from Luxury}
  \]
  So Lee prefers **Luxury**.

- If Xi chooses **Luxury**, Lee gets:
  \[
  0.5 \text{ from Modest}, \quad 1 \text{ from Luxury}
  \]
  So Lee again prefers **Luxury**.

Thus **Luxury strictly dominates Modest** for Lee.

By symmetry, the same is true for Xi:

- If Lee chooses Modest, Xi prefers Luxury because \(2.5>2\).
- If Lee chooses Luxury, Xi prefers Luxury because \(1>0.5\).

Therefore both families have a strictly dominant strategy: **Luxury**.

So the unique Nash equilibrium is:

\[
(\text{Luxury},\text{Luxury})
\]

with payoffs:

\[
(1,1)
\]

### Social desirability

This outcome is socially undesirable. Compare total payoffs:

- Both modest:
  \[
  2+2=4
  \]

- Both luxury:
  \[
  1+1=2
  \]

The outcome \((\text{Modest},\text{Modest})\) gives both families a higher payoff than \((\text{Luxury},\text{Luxury})\). It is a **Pareto improvement** over the Nash equilibrium.

So the game is similar to a **Prisoner’s Dilemma**: individually rational behavior leads to a collectively inefficient outcome. Each family buys a luxury car to avoid falling behind, but when both do so, the status gain disappears and both are worse off.

---

## (c) Policy yielding a socially preferable outcome

A reasonable policy is a **tax or registration fee on luxury cars**. This can be interpreted as a tax on positional/status consumption, similar to a Pigouvian tax. The idea is that buying a luxury car imposes a negative externality on the neighbor by making them feel relatively worse off, so the tax discourages the luxury choice.

Suppose the government imposes a luxury-car tax equal to **1 payoff unit** on any family that buys a luxury car. Then each luxury buyer’s payoff falls by 1.

The new payoff matrix becomes:

\[
\begin{array}{c|cc}
 & \text{Xi Modest} & \text{Xi Luxury} \\
\hline
\text{Lee Modest} & (2,2) & (0.5,1.5) \\
\text{Lee Luxury} & (1.5,0.5) & (0,0)
\end{array}
\]

Now consider Lee’s incentives.

- If Xi chooses **Modest**, Lee gets:
  \[
  2 \text{ from Modest}, \quad 1.5 \text{ from Luxury}
  \]
  So Lee prefers **Modest**.

- If Xi chooses **Luxury**, Lee gets:
  \[
  0.5 \text{ from Modest}, \quad 0 \text{ from Luxury}
  \]
  So Lee again prefers **Modest**.

Thus **Modest strictly dominates Luxury** for Lee.

By symmetry, Modest also strictly dominates Luxury for Xi.

Therefore the new unique Nash equilibrium is:

\[
(\text{Modest},\text{Modest})
\]

with payoffs:

\[
(2,2)
\]

This is socially preferable because total welfare is now:

\[
2+2=4
\]

instead of the original Nash-equilibrium welfare:

\[
1+1=2
\]

More generally, any luxury tax greater than \(0.5\) payoff units would be enough to make Modest the privately optimal choice.

---

## (d) Why observed behavior in a nearby suburb may differ from the one-shot prediction

The prediction in part (b) comes from a **one-shot simultaneous game**. In that version, each family chooses once, independently, and cannot punish or reward the other family later. Under those assumptions, the unique Nash equilibrium is for both families to buy luxury cars.

But the nearby suburb is different. Families replace cars every few years and observe each other’s choices closely. That means the interaction is better modeled as a **repeated game**, not a one-shot game.

In a repeated game, families can condition their current behavior on past behavior. This can support cooperation.

Suppose the families use the following strategy:

- Buy a modest car as long as the other family has always bought modest cars.
- If the other family ever buys a luxury car, punish them by buying luxury cars in all future periods.

This is a version of a **grim-trigger strategy**.

Now compare the payoff from cooperating with the payoff from deviating.

If both families continue buying modest cars forever, each family receives:

\[
2+2\delta+2\delta^2+\cdots=\frac{2}{1-\delta}
\]

where \(\delta\) is the discount factor.

If Lee deviates by buying a luxury car while Xi buys a modest car, Lee gets a one-period payoff of \(2.5\). But after that, Xi punishes by buying luxury cars forever, so Lee receives \(1\) in every future period. Lee’s payoff from deviation is:

\[
2.5+\delta+\delta^2+\cdots
\]

\[
=2.5+\frac{\delta}{1-\delta}
\]

Cooperation is sustainable if:

\[
\frac{2}{1-\delta} \geq 2.5+\frac{\delta}{1-\delta}
\]

Multiplying both sides by \(1-\delta\):

\[
2 \geq 2.5(1-\delta)+\delta
\]

\[
2 \geq 2.5-2.5\delta+\delta
\]

\[
2 \geq 2.5-1.5\delta
\]

\[
1.5\delta \geq 0.5
\]

\[
\delta \geq \frac{1}{3}
\]

So if families are sufficiently patient, specifically if:

\[
\delta \geq \frac{1}{3},
\]

then buying modest cars can be sustained as an equilibrium of the repeated game.

This explains why the observed choices can be at odds with the one-shot prediction. In the one-shot game, each family wants to buy luxury to gain status or avoid inferiority. But in the repeated game, buying luxury today may trigger a future status arms race in which everyone buys luxury cars and everyone is worse off.

Thus, families may rationally choose modest cars because they care about the future and because their choices are observable. Social norms, reputation, and the threat of future retaliation can support the cooperative outcome:

\[
(\text{Modest},\text{Modest})
\]

even though the one-shot Nash equilibrium is:

\[
(\text{Luxury},\text{Luxury})
\]

So the survey finding is not necessarily inconsistent with the preferences in part (a). It shows that the relevant game in the suburb is not a one-period Prisoner’s Dilemma, but a repeated social interaction where cooperation can be sustained.

### Judge Feedback

### (a) Narrative consistent with payoff matrix — **6/6**

- **Consistent narrative: 4/4**  
  The student provides a fully consistent story explaining all four payoff pairs using material benefits/costs and relative status effects. The numerical payoff construction exactly reproduces the given matrix.

- **Reference to conspicuous consumption / keeping up with the Joneses / externality: 2/2**  
  The answer explicitly identifies the situation as “status competition” and “keeping up with the neighbors,” with a clear negative positional externality.

**Score for (a): 6/6**

---

### (b) Nash equilibrium and social desirability — **6/6**

- **States unique Nash equilibrium: 1/1**  
  Correctly states that the unique Nash equilibrium is **(Luxury, Luxury)**.

- **Correct reasoning: 3/3**  
  The student correctly shows that Luxury strictly dominates Modest for both Lee and Xi.

- **Social desirability / Pareto inefficiency: 2/2**  
  Correctly explains that the Nash equilibrium is socially undesirable and Pareto inefficient because both families would be better off at **(Modest, Modest)**, with payoffs \((2,2)\) instead of \((1,1)\).

**Score for (b): 6/6**

---

### (c) Policy and new payoff matrix — **8/8**

- **Reasonable policy yielding Pareto-improving outcome: 4/4**  
  The student proposes a luxury-car tax, correctly interpreting it as a Pigouvian-style tax on positional consumption. This is a reasonable policy and it changes incentives so that the socially preferable outcome is achieved.

- **Consistent payoff matrix: 4/4**  
  The new payoff matrix correctly subtracts 1 payoff unit from any family buying a luxury car:

  \[
  \begin{array}{c|cc}
   & \text{Xi Modest} & \text{Xi Luxury} \\
  \hline
  \text{Lee Modest} & (2,2) & (0.5,1.5) \\
  \text{Lee Luxury} & (1.5,0.5) & (0,0)
  \end{array}
  \]

  The student correctly verifies that **Modest** becomes the strictly dominant strategy for both, making **(Modest, Modest)** the new unique Nash equilibrium.

**Score for (c): 8/8**

---

### (d) Repeated-game explanation — **10/10**

- **Identifies repetition as the key element: 2/2**  
  The student clearly explains that the nearby suburb should be modeled as a repeated game rather than a one-shot game.

- **Well-argued reason consistent with observations: 4/4**  
  The answer correctly explains why observed modest-car choices can differ from the one-shot prediction: future consequences, observability, reputation, and the threat of future retaliation can sustain cooperation.

- **Strategy sustaining the cooperative equilibrium: 4/4**  
  The student describes a grim-trigger strategy: buy modest cars unless someone deviates, after which luxury cars are bought forever. The answer also provides a correct incentive-compatibility calculation showing that cooperation is sustainable if \(\delta \geq 1/3\).

**Score for (d): 10/10**

---

TOTAL: 30/30

---
