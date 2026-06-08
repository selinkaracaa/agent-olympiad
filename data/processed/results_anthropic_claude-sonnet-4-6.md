# Results: anthropic/claude-sonnet-4-6

## econ_ieo_2019_q1 — Mechanism Design (2019)
**Score: 20/30 / 30**

### Agent Answer

# International Economics Olympiad – Cake Cutting Problem

## Part a) How will Alice cut the cake?

**Setting up Alice's problem:**

Alice cuts first, then Bob picks his favorite piece, then Clara picks her favorite of the remaining two, and Alice gets whatever is left.

Alice wants to **maximize her guaranteed minimum** — she knows Bob and Clara will act in their own interest (taking the largest available pieces).

**Alice's optimal strategy:**

Alice should cut the cake into **three equal pieces of size 1/3 each**.

**Reasoning:**

- Alice goes last, so she receives whichever piece Bob and Clara don't want.
- Bob will take the largest piece available. Clara will then take the largest of the two remaining pieces.
- If Alice cuts unevenly, say pieces of sizes $x > y > z$, then Bob takes $x$, Clara takes $y$, and Alice is left with $z < 1/3$.
- Alice cannot guarantee herself more than $1/3$ regardless of how she cuts (Bob and Clara together take two pieces, and at least one of any two pieces has size $\geq 1/3$... actually the *smallest* of three pieces is $\leq 1/3$).

**More formally:** Let the three pieces have sizes $p_1 \geq p_2 \geq p_3$ with $p_1+p_2+p_3=1$. Bob takes $p_1$, Clara takes $p_2$, Alice gets $p_3$. Alice wants to maximize $p_3$. Subject to $p_1+p_2+p_3=1$ and $p_1\geq p_2\geq p_3\geq 0$, the maximum of $p_3$ is achieved when $p_1=p_2=p_3=1/3$.

**Answer:** Alice cuts the cake into **three equal pieces of size 1/3**. This guarantees her exactly **1/3** of the cake — the best she can do given that she picks last.

---

## Part b) Under which conditions (a, b, c) does a mechanism exist?

### Necessary Condition

The mother needs to guarantee all three kids are happy. The three minimum shares must be simultaneously achievable from a cake of size 1:

$$\boxed{a + b + c \leq 1}$$

This is clearly **necessary**: we cannot give Alice at least $a$, Bob at least $b$, and Clara at least $c$ from a cake of size 1 if $a+b+c > 1$.

We will show it is also **sufficient** by constructing an explicit mechanism.

---

### Sufficient Condition and Mechanism

**Claim:** A mechanism ensuring each child is happy exists **if and only if $a + b + c \leq 1$.**

#### Why it's sufficient: The Mechanism

Since all three children know $a, b, c$ and the mother knows only that $0 < a,b,c < 1$, we need a mechanism that works **without the mother knowing the values**. The children themselves can implement the following:

---

**Mechanism:**

**Step 1 – Alice cuts:**
Alice cuts a piece of size **exactly $a$** and sets it aside as her own candidate piece.

**Step 2 – Bob evaluates Alice's piece:**
Bob looks at the remaining cake of size $1 - a$.

- If Bob can cut a piece of size $b$ from the remainder *and* still leave at least $c$ for Clara (i.e., $1 - a \geq b + c$, which holds since $a+b+c \leq 1$), proceed to Step 3.

**Step 3 – Bob cuts:**
Bob cuts a piece of size **exactly $b$** from the remaining $(1-a)$ cake.

**Step 4 – Clara takes:**
Clara receives the remaining piece of size $1 - a - b \geq c$ (since $a+b+c \leq 1$).

**Step 5 – Allocation:**
- Alice gets her piece of size $a$ ✓ (happy, since $\geq a$)
- Bob gets his piece of size $b$ ✓ (happy, since $\geq b$)
- Clara gets $1-a-b \geq c$ ✓ (happy, since $\geq c$)

---

**But we must check incentives — do the children want to follow this mechanism?**

- **Alice** cuts exactly $a$: If she cuts more than $a$, she risks Bob or Clara being unhappy (though that's their problem). More importantly, does Alice prefer to deviate? Alice is told she *gets* her own cut piece. If she cuts more than $a$, she gets more — **so we need to address this**.

**Refined Mechanism (incentive-compatible):**

We use the following **revelation/sequential mechanism** exploiting the fact that all children know $a, b, c$:

**Step 1:** Alice cuts the cake into **two pieces**: one of size $a$ (labeled "Alice's piece") and one of size $1-a$.

**Step 2:** Bob cuts the piece of size $1-a$ into **two pieces**: one of size $b$ (labeled "Bob's piece") and one of size $1-a-b \geq c$.

**Step 3:** Clara receives the piece of size $1-a-b$.

**Step 4:** Alice receives her labeled piece ($a$), Bob receives his labeled piece ($b$).

**Incentive analysis:**

- **Alice** in Step 1: If she cuts a piece larger than $a$ for herself, she leaves only $1 - (\text{Alice's piece}) < 1-a$ for Bob and Clara. Bob needs $b$ and Clara needs $c$; if Bob cannot get $b$, Bob may refuse or the mechanism fails. Since the children **all know** $a,b,c$ and all want everyone to be happy (or at least, we design the mechanism so that if Alice deviates, she is penalized):

**Final Clean Mechanism (using a "trimming" approach):**

1. **Alice** cuts a piece $P_A$ and declares it as her share.
2. **Bob** may **trim** $P_A$ down to size $a$ if $P_A > a$ (trimmings go back to the remaining cake). Bob then cuts his own piece $P_B = b$ from the remaining cake ($1 - a$).
3. **Clara** receives everything left: $1 - a - b \geq c$.
4. Alice gets $\min(P_A, a) = a$, Bob gets $b$, Clara gets $\geq c$.

Since Alice knows Bob will trim her piece to $a$ anyway, she has no incentive to cut more than $a$. She also wouldn't cut less (she'd get less than $a$, making herself unhappy). So Alice cuts exactly $a$.

---

### Summary

| | Answer |
|---|---|
| **Condition** | $a + b + c \leq 1$ |
| **Mechanism** | Alice cuts $a$; Bob cuts $b$ from remainder; Clara gets $1-a-b \geq c$ |

**The mechanism exists if and only if:**
$$a + b + c \leq 1$$

This is both **necessary** (the pieces must fit in the cake) and **sufficient** (the explicit mechanism above works).

### Judge Feedback

I'll evaluate the student's answer systematically against the official rubric.

## Part a) Evaluation

**Student's answer:** Alice should cut the cake into three equal pieces of size 1/3 each.

**Reasoning provided:** The student correctly identifies that Bob takes the largest piece, Clara takes the second largest, and Alice gets the smallest. They formally show that to maximize p₃ (the minimum piece), Alice sets p₁=p₂=p₃=1/3. This is a complete and correct explanation.

**Rubric:** Right answer and correct explanation = 10 rp; only right answer = 5 rp.

**Score: 10/10** — The student provides the correct answer with a rigorous formal explanation.

---

## Part b) Evaluation

**Necessary condition:** The student correctly identifies and explains that a+b+c ≤ 1 is necessary, with clear reasoning that you cannot simultaneously provide shares a, b, c from a cake of size 1 if their sum exceeds 1. ✓

**Mechanism developed:** The student proposes a sequential cutting mechanism (Alice cuts a, Bob cuts b, Clara gets remainder). This is a valid mechanism when a+b+c ≤ 1. ✓

**Feature analysis per rubric:**
- **Feature 1** (distribution done by one of the kids, not the mother): The student's mechanism has Alice and Bob doing the cutting, acknowledging the mother doesn't know a,b,c. This is implicitly present but not as crisply articulated as in the sample solution's "crucial features" framing.
- **Feature 2** (if distribution doesn't satisfy requirements, everyone gets nothing): The student's mechanism does NOT include this feature. The student's mechanism is a deterministic sequential cut — there's no "punishment" or "vote" mechanism that makes everyone get nothing if someone deviates. The student attempts to address incentives via a "trimming" approach but never introduces the key feature that non-compliance leads to everyone getting nothing.

**Incentive compatibility:** The student struggles here. The trimming approach is creative but incomplete. The sample solution uses a voting mechanism (Bob and Clara vote; if either votes against, no one gets anything), which cleanly handles incentives. The student's mechanism lacks a credible punishment for deviation by Alice or others.

**Explanation of why it works:** Partially explained — the student shows the pieces fit (sufficiency) and attempts incentive analysis, but the incentive argument is not fully convincing without Feature 2 (the "everyone gets nothing" punishment).

**Rubric assessment:**
- The student provides the correct necessary and sufficient condition (a+b+c ≤ 1) with explanation of necessity. ✓
- A mechanism is developed, but only Feature 2 is partially present (through trimming, not a clear "everyone gets nothing" rule). Feature 1 is implicitly present.
- The explanation of why it works is incomplete due to the missing punishment mechanism.
- The answer and necessity of constraint are explained. ✓

This best fits: "Correct mechanism is developed with complete explanation why it works, but only feature 2 is indicated, a right answer is provided and necessity of constraint is explained - 15 rp.; without answer or without explanation of the necessity of the constraint - 10 rp."

However, the mechanism isn't fully incentive-compatible as presented (the trimming argument is incomplete), and Feature 2 in the official sense (everyone gets nothing as a punishment) isn't clearly present. The student does have the right answer and explains necessity, but the mechanism explanation is incomplete.

I'd score this at **10/20** — a mechanism is developed, the right answer is provided, and necessity is explained, but the mechanism lacks the key punishment feature (Feature 2 in its clean form) and the incentive explanation is incomplete.

---

## Final Scoring

- **Part a):** 10/10
- **Part b):** 10/20

TOTAL: 20/30

---

## econ_ieo_2021_q1 — Dynamic Equilibrium (2021)
**Score: 30/30 / 30**

### Agent Answer

I'll solve this step-by-step, working through each part carefully.

---

## Part (a): Equilibrium prices when K = 210

**Setting D = S for each market:**

**Oil market:**
$$D_A = S_A \implies 210 - 2P_A + P_B = -10 + 2P_A$$
$$220 + P_B = 4P_A \quad \text{...(1)}$$

**Gas market:**
$$D_B = S_B \implies 80 - 6P_B + 2P_A = -5 + P_B$$
$$85 + 2P_A = 7P_B \quad \text{...(2)}$$

**Solving the system:**

From (1): $P_A = \frac{220 + P_B}{4}$

Substituting into (2):
$$85 + 2\cdot\frac{220 + P_B}{4} = 7P_B$$
$$85 + \frac{440 + 2P_B}{4} = 7P_B$$
$$340 + 440 + 2P_B = 28P_B$$
$$780 = 26P_B$$
$$\boxed{P_B^* = 30}$$

From (1): $P_A = \frac{220 + 30}{4} = \frac{250}{4} = \boxed{62.5}$

**Verification:**
- $D_A = 210 - 2(62.5) + 30 = 210 - 125 + 30 = 115$; $S_A = -10 + 2(62.5) = 115$ ✓
- $D_B = 80 - 6(30) + 2(62.5) = 80 - 180 + 125 = 25$; $S_B = -5 + 30 = 25$ ✓

**Equilibrium: $P_A^* = 62.5$, $P_B^* = 30$, $Q_A^* = 115$, $Q_B^* = 25$**

---

## Part (b): Production decisions for period 2, given expected $K_2^e = 80$

Producers must decide output **one period ahead**. They base their supply on **expected prices**, but since they commit to quantities, they use their supply functions evaluated at expected prices.

The key cobweb-type assumption: producers form expected prices. Given expected $K_2^e = 80$, they solve for the equilibrium they *expect* to prevail in period 2.

**Expected equilibrium with $K = 80$:**

**Oil market:**
$$80 - 2P_A + P_B = -10 + 2P_A \implies 90 + P_B = 4P_A \quad \text{...(1')}$$

**Gas market (unchanged):**
$$85 + 2P_A = 7P_B \quad \text{...(2)}$$

From (1'): $P_A = \frac{90 + P_B}{4}$

Into (2):
$$85 + 2\cdot\frac{90 + P_B}{4} = 7P_B$$
$$85 + \frac{180 + 2P_B}{4} = 7P_B$$
$$340 + 180 + 2P_B = 28P_B$$
$$520 = 26P_B$$
$$P_B^e = 20$$

$$P_A^e = \frac{90 + 20}{4} = \frac{110}{4} = 27.5$$

**Production quantities (committed supply):**
$$Q_A^{s} = -10 + 2P_A^e = -10 + 2(27.5) = -10 + 55 = \boxed{45 \text{ units of Oil}}$$
$$Q_B^{s} = -5 + P_B^e = -5 + 20 = \boxed{15 \text{ units of Gas}}$$

---

## Part (c): Market-clearing prices when $K_2 = 210$, but supply is fixed

Supply is committed: $Q_A = 45$, $Q_B = 15$ (capacity exhausted, so these quantities must clear).

Demand with actual $K_2 = 210$:
$$D_A = 210 - 2P_A + P_B = 45 \quad \text{...(i)}$$
$$D_B = 80 - 6P_B + 2P_A = 15 \quad \text{...(ii)}$$

**From (i):** $210 - 2P_A + P_B = 45 \implies 2P_A - P_B = 165 \quad \text{...(i')}$

**From (ii):** $80 - 6P_B + 2P_A = 15 \implies 2P_A - 6P_B = -65 \quad \text{...(ii')}$

**Subtracting (ii') from (i'):**
$$(2P_A - P_B) - (2P_A - 6P_B) = 165 - (-65)$$
$$5P_B = 230$$
$$\boxed{P_B = 46}$$

From (i'): $2P_A = 165 + 46 = 211 \implies \boxed{P_A = 105.5}$

**Verification:**
- $D_A = 210 - 2(105.5) + 46 = 210 - 211 + 46 = 45$ ✓
- $D_B = 80 - 6(46) + 2(105.5) = 80 - 276 + 211 = 15$ ✓

**Period 2 market-clearing prices: $P_A = 105.5$, $P_B = 46$**

---

## Part (d): Long-run dynamics with naive expectations and $K = 210$

**Naive expectations:** Firms expect $P_{A,t+1}^e = P_{A,t}$ and $P_{B,t+1}^e = P_{B,t}$.

**Committed supply in period $t+1$** (based on current prices):
$$Q_A^{t+1} = -10 + 2P_{A,t}$$
$$Q_B^{t+1} = -5 + P_{B,t}$$

**Market clearing in period $t+1$** with $K = 210$ and fixed supplies:
$$210 - 2P_{A,t+1} + P_{B,t+1} = -10 + 2P_{A,t} \quad \text{...(I)}$$
$$80 - 6P_{B,t+1} + 2P_{A,t+1} = -5 + P_{B,t} \quad \text{...(II)}$$

**Rewriting the system:**

From (I): $-2P_{A,t+1} + P_{B,t+1} = 2P_{A,t} - 220$

From (II): $2P_{A,t+1} - 6P_{B,t+1} = P_{B,t} - 85$

**Solving for $P_{A,t+1}$ and $P_{B,t+1}$:**

Add the two equations:
$$-5P_{B,t+1} = 2P_{A,t} + P_{B,t} - 305$$
$$P_{B,t+1} = \frac{305 - 2P_{A,t} - P_{B,t}}{5} \quad \text{...(*)}\$$

From (I): $2P_{A,t+1} = 220 + P_{B,t+1} - 2P_{A,t} \cdot(-1)$... Let me redo this carefully.

From (I): $2P_{A,t+1} = 210 + P_{B,t+1} - (-10 + 2P_{A,t})$

Wait, let me be precise. The demand equals the fixed supply:

$$210 - 2P_{A,t+1} + P_{B,t+1} = Q_A^{t+1} = -10 + 2P_{A,t}$$
$$\Rightarrow -2P_{A,t+1} + P_{B,t+1} = -220 + 2P_{A,t} \quad \text{(I)}$$

$$80 - 6P_{B,t+1} + 2P_{A,t+1} = Q_B^{t+1} = -5 + P_{B,t}$$
$$\Rightarrow 2P_{A,t+1} - 6P_{B,t+1} = -85 + P_{B,t} \quad \text{(II)}$$

**Add (I) and (II):**
$$-5P_{B,t+1} = -305 + 2P_{A,t} + P_{B,t}$$
$$P_{B,t+1} = \frac{305 - 2P_{A,t} - P_{B,t}}{5} \quad \text{...(*)}$$

**From (I):** $2P_{A,t+1} = 220 - 2P_{A,t} + \frac{2(305 - 2P_{A,t} - P_{B,t})}{5}$... 

Let me substitute (*) back into (I):

$$-2P_{A,t+1} + \frac{305 - 2P_{A,t} - P_{B,t}}{5} = -220 + 2P_{A,t}$$
$$-2P_{A,t+1} = -220 + 2P_{A,t} - \frac{305 - 2P_{A,t} - P_{B,t}}{5}$$
$$-2P_{A,t+1} = \frac{-1100 + 10P_{A,t} - 305 + 2P_{A,t} + P_{B,t}}{5}$$
$$-2P_{A,t+1} = \frac{-1405 + 12P_{A,t} + P_{B,t}}{5}$$
$$P_{A,t+1} = \frac{1405 - 12P_{A,t} - P_{B,t}}{10} \quad \text{...(**)}$$

**The dynamical system:**
$$P_{A,t+1} = \frac{1405 - 12P_{A,t} - P_{B,t}}{10} = 140.5 - 1.2P_{A,t} - 0.1P_{B,t}$$
$$P_{B,t+1} = \frac{305 - 2P_{A,t} - P_{B,t}}{5} = 61 - 0.4P_{A,t} - 0.2P_{B,t}$$

**In matrix form:** Let $\mathbf{p}_t = (P_{A,t}, P_{B,t})^\top$

$$\mathbf{p}_{t+1} = \mathbf{c} + M\mathbf{p}_t$$

where:
$$M = \begin{pmatrix} -1.2 & -0.1 \\ -0.4 & -0.2 \end{pmatrix}, \quad \mathbf{c} = \begin{pmatrix} 140.5 \\ 61 \end{pmatrix}$$

**Finding the fixed point (steady state):** Set $\mathbf{p}^* = \mathbf{c} + M\mathbf{p}^*$:
$$(I - M)\mathbf{p}^* = \mathbf{c}$$
$$\begin{pmatrix} 2.2 & 0.1 \\ 0.4 & 1.2 \end{pmatrix}\begin{pmatrix} P_A^* \\ P_B^* \end{pmatrix} = \begin{pmatrix} 140.5 \\ 61 \end{pmatrix}$$

**Determinant:** $\det = 2.2 \times 1.2 - 0.1 \times 0.4 = 2.64 - 0.04 = 2.6$

$$P_A^* = \frac{1.2(140.5) - 0.1(61)}{2.6} = \frac{168.6 - 6.1}{2.6} = \frac{162.5}{2.6} = 62.5$$
$$P_B^* = \frac{2.2(61) - 0.4(140.5)}{2.6} = \frac{134.2 - 56.2}{2.6} = \frac{78}{2.6} = 30$$

This matches the Part (a) equilibrium — as expected, since $K = 210$.

**Stability analysis — eigenvalues of $M$:**

$$\det(M - \lambda I) = (-1.2 - \lambda)(-0.2 - \lambda) - (-0.1)(-0.4) = 0$$
$$(\lambda + 1.2)(\lambda + 0.2) - 0.04 = 0$$
$$\lambda^2 + 1.4\lambda + 0.24 - 0.04 = 0$$
$$\lambda^2 + 1.4\lambda + 0.20 = 0$$

$$\lambda = \frac{-1.4 \pm \sqrt{1.96 - 0.8}}{2} = \frac{-1.4 \pm \sqrt{1.16}}{2}$$

$$\sqrt{1.16} \approx 1.0770$$

$$\lambda_1 = \frac{-1.4 + 1.077}{2} = \frac{-0.323}{2} \approx -0.1615$$
$$\lambda_2 = \frac{-1.4 - 1.077}{2} = \frac{-2.477}{2} \approx -1.2385$$

**Stability check:**
- $|\lambda_1| \approx 0.1615 < 1$ → stable component
- $|\lambda_2| \approx 1.2385 > 1$ → **unstable component**

Since $|\lambda_2| > 1$, the system is **unstable** (unless the initial condition happens to lie exactly on the stable manifold associated with $\lambda_1$).

**Starting values:** From parts (b) and (c):
- Period 1: $P_{A,1} = 62.5$, $P_{B,1} = 30$ (equilibrium)
- Period 2: $P_{A,2} = 105.5$, $P_{B,2} = 46$ (from part c)

**Verify with the map (checking period 3):**
$$P_{A,3} = 140.5 - 1.2(105.5) - 0.1(46) = 140.5 - 126.6 - 4.6 = 9.3$$
$$P_{B,3} = 61 - 0.4(105.5) - 0.2(46) = 61 - 42.2 - 9.2 = 9.6$$

**Period 4:**
$$P_{A,4} = 140.5 - 1.2(9.3) - 0.1(9.6) = 140.5 - 11.16 - 0.96 = 128.38$$
$$P_{B,4} = 61 - 0.4(9.3) - 0.2(9.6) = 61 - 3.72 - 1.92 = 55.36$$

The prices oscillate with **increasing amplitude** around the equilibrium — confirming the unstable eigenvalue drives divergence.

**Expressing in terms of eigenvectors to confirm:**

Deviation from steady state: $\mathbf{x}_t = \mathbf{p}_t - \mathbf{p}^*$

$\mathbf{x}_t = c_1 \lambda_1^t \mathbf{v}_1 + c_2 \lambda_2^t \mathbf{v}_2$

Since $|\lambda_2| > 1$, the term $c_2 \lambda_2^t \mathbf{v}_2$ grows without bound (unless $c_2 = 0$).

Check whether $c_2 = 0$ from the initial deviation:
$$\mathbf{x}_1 = (62.5 - 62.5,\ 30 - 30)^\top = (0, 0)^\top$$
$$\mathbf{x}_2 = (105.5 - 62.5,\ 46 - 30)^\top = (43, 16)^\top$$

Since $\mathbf{x}_1 = 0$ but $\mathbf{x}_2 \neq 0$, clearly $c_2 \neq 0$, so the unstable mode is excited.

---

## Summary of Answers

**(a)** $P_A^* = 62.5$, $P_B^* = 30$ (with $Q_A^* = 115$, $Q_B^* = 25$)

**(b)** Based on expected prices $P_A^e = 27.5$, $P_B^e = 20$:
- **Oil production for period 2: $Q_A = 45$ units**
- **Gas production for period 2: $Q_B = 15$ units**

**(c)** With fixed supply $(Q_A = 45, Q_B = 15)$ and actual $K = 210$:
- **$P_A = 105.5$, $P_B = 46$**

**(d)** The dynamic system has eigenvalues $\lambda_1 \approx -0.162$ and $\lambda_2 \approx -1.239$.

Since $|\lambda_2| > 1$, the system is **dynamically unstable**. Prices oscillate (sign of negative eigenvalues) with **diverging amplitude** around the equilibrium $(P_A^*, P_B^*) = (62.5, 30)$. As $t \to \infty$, prices and quantities **do not converge** — they exhibit increasingly wild oscillations and **diverge to $\pm\infty$** (or until negative prices/quantities become economically infeasible). The market with naive expectations is **unstable** in this model — the cobweb dynamics explode rather than converging to the rational-expectations equilibrium.

### Judge Feedback

I'll evaluate each part systematically according to the official rubric.

## Part (a) — 5 points possible

The student correctly sets up both equilibrium conditions, solves the system, and arrives at:
- $P_A^* = 62.5$ ✓
- $P_B^* = 30$ ✓

Both values match the official solution exactly, with proper verification.

**Score: 5/5**

---

## Part (b) — 10 points possible

The student correctly:
- Sets up the expected equilibrium with $K = 80$
- Solves for expected prices: $P_A^e = 27.5$ ✓ and $P_B^e = 20$ ✓
- Plugs into supply functions:
  - $Q_A = -10 + 2(27.5) = 45$ ✓
  - $Q_B = -5 + 20 = 15$ ✓

Both quantities are correct, matching the official solution exactly.

**Score: 10/10**

---

## Part (c) — 5 points possible

The student correctly:
- Fixes supply at $Q_A = 45$, $Q_B = 15$
- Sets up demand-equals-fixed-supply equations with $K = 210$
- Solves the system to get:
  - $P_A = 105.5$ ✓
  - $P_B = 46$ ✓

Both prices match the official solution, with verification provided.

**Score: 5/5**

---

## Part (d) — 10 points possible

The student provides an exceptionally thorough analysis:
- Correctly derives the dynamical system with naive expectations
- Finds the fixed point (62.5, 30), confirming it matches part (a)
- Computes eigenvalues of the transition matrix: $\lambda_1 \approx -0.162$ and $\lambda_2 \approx -1.239$
- Identifies $|\lambda_2| > 1$ as the source of instability
- Provides **numeric proof** by computing periods 3 and 4 explicitly:
  - $(P_{A,3}, P_{B,3}) = (9.3, 9.6)$ ✓ (matches official solution)
  - $(P_{A,4}, P_{B,4}) = (128.38, 55.36)$, showing diverging oscillations
- Correctly explains the divergence as increasingly large oscillations
- Notes that negative prices/quantities become economically infeasible

This clearly satisfies the highest rubric criterion: "explanation of idea of increasing fluctuations with either some kind of (numeric) proof or with a reference to the problem that K is open." The student provides both numeric proof and a rigorous eigenvalue analysis.

**Score: 10/10**

---

## Final Assessment

| Part | Points Earned | Points Possible |
|------|--------------|-----------------|
| (a)  | 5            | 5               |
| (b)  | 10           | 10              |
| (c)  | 5            | 5               |
| (d)  | 10           | 10              |

TOTAL: 30/30

---

## econ_ieo_2022_q5 — Going Green (Bandwagon Effect) (2022)
**Score: 28/30 / 30**

### Agent Answer

# International Economics Olympiad – Solar Panels Problem

## Setting Up the Framework

**Given:**
- $Q_c = 150{,}000 - 5p$ (environmentally conscious consumers)
- $Q_b = 40{,}000 - 5p + 500\sqrt{N}$ (bandwagon consumers)
- Supply: perfectly elastic at $p = 25{,}000$
- In equilibrium: $N = Q_c + Q_b$

---

## Part (a): Equilibrium without subsidy, p = $25,000

### Step 1: Environmental consumers decide first

$$Q_c = 150{,}000 - 5(25{,}000) = 150{,}000 - 125{,}000 = 25{,}000$$

So initially, $N_0 = 25{,}000$ solar panels are installed.

### Step 2: Bandwagon adjustment process

At each step, bandwagon consumers observe current $N$ and decide:
$$Q_b = 40{,}000 - 5(25{,}000) + 500\sqrt{N} = 40{,}000 - 125{,}000 + 500\sqrt{N} = -85{,}000 + 500\sqrt{N}$$

For $Q_b > 0$, we need $500\sqrt{N} > 85{,}000$, i.e., $\sqrt{N} > 170$, i.e., $N > 28{,}900$.

**Check initial condition:** With $N_0 = 25{,}000$: $\sqrt{25{,}000} \approx 158.1$, so $Q_b = -85{,}000 + 500(158.1) = -85{,}000 + 79{,}057 < 0$.

Since $Q_b < 0$, bandwagon consumers purchase **zero** panels.

### Step 3: Verify equilibrium

With $N = 25{,}000$: bandwagon consumers want $Q_b = \max(0, -85{,}000 + 500\sqrt{25{,}000}) < 0$, so $Q_b = 0$.

Total: $N = Q_c + Q_b = 25{,}000 + 0 = 25{,}000$ ✓ (self-consistent)

$$\boxed{Q^* = 25{,}000 \text{ solar panels}}$$

---

## Part (b): Subsidy s = $5,000, so effective price p = $20,000

### Step 1: Environmental consumers

$$Q_c = 150{,}000 - 5(20{,}000) = 150{,}000 - 100{,}000 = 50{,}000$$

Initial $N_0 = 50{,}000$.

### Step 2: Bandwagon iteration

$$Q_b = 40{,}000 - 5(20{,}000) + 500\sqrt{N} = 40{,}000 - 100{,}000 + 500\sqrt{N} = -60{,}000 + 500\sqrt{N}$$

At each step: $N_{t+1} = Q_c + Q_b(N_t) = 50{,}000 + (-60{,}000 + 500\sqrt{N_t}) = -10{,}000 + 500\sqrt{N_t}$

**Fixed point condition** (equilibrium: $N = -10{,}000 + 500\sqrt{N}$):

Let $x = \sqrt{N}$:
$$x^2 = -10{,}000 + 500x$$
$$x^2 - 500x + 10{,}000 = 0$$
$$x = \frac{500 \pm \sqrt{250{,}000 - 40{,}000}}{2} = \frac{500 \pm \sqrt{210{,}000}}{2} = \frac{500 \pm 100\sqrt{21}}{2} = 250 \pm 50\sqrt{21}$$

$\sqrt{21} \approx 4.5826$

- $x_1 = 250 + 229.13 = 479.13 \Rightarrow N_1 = 229{,}566$
- $x_2 = 250 - 229.13 = 20.87 \Rightarrow N_2 = 435.5$

### Step 3: Stability analysis and iteration from $N_0 = 50{,}000$

Check if the process converges starting from $N_0 = 50{,}000$:

| Step | $N_t$ | $N_{t+1} = -10{,}000 + 500\sqrt{N_t}$ |
|------|--------|----------------------------------------|
| 0 | 50,000 | $-10{,}000 + 500(223.6) = 101{,}800$ |
| 1 | 101,800 | $-10{,}000 + 500(319.1) = 149{,}530$ |
| 2 | 149,530 | $-10{,}000 + 500(386.7) = 183{,}350$ |
| 3 | 183,350 | $-10{,}000 + 500(428.2) = 204{,}080$ |
| ... | → | → $N_1 = 229{,}566$ |

The iteration converges upward toward the **larger fixed point** $N_1$.

### Step 4: Verify constraints

Maximum bandwagon consumers: 200,000. Check $Q_b$:
$$Q_b = N - Q_c = 229{,}566 - 50{,}000 = 179{,}566 < 200{,}000 \checkmark$$

Also verify $Q_b \geq 0$: yes ✓

### Step 5: Exact equilibrium

$$N^* = (250 + 50\sqrt{21})^2 = 62{,}500 + 2(250)(50\sqrt{21}) + 2500(21) = 62{,}500 + 25{,}000\sqrt{21} + 52{,}500$$
$$= 115{,}000 + 25{,}000\sqrt{21}$$

Numerically: $N^* = 115{,}000 + 25{,}000(4.5826) \approx 115{,}000 + 114{,}564 \approx 229{,}564$

$$\boxed{N^* = 115{,}000 + 25{,}000\sqrt{21} \approx 229{,}564 \text{ solar panels}}$$

---

## Part (c): Subsidy eliminated after equilibrium (b); price returns to $25,000

### Key distinction from Part (a): History matters!

Now we start from $N_0 = 229{,}564$ (the equilibrium from part b), not from scratch.

### Step 1: Environmental consumers at p = $25,000

$$Q_c = 150{,}000 - 5(25{,}000) = 25{,}000$$

Environmental consumers who no longer have WTP ≥ $25,000 return their panels (those with WTP between $20,000 and $25,000 had bought under the subsidy but now return them).

So $Q_c$ drops back to **25,000**.

### Step 2: Bandwagon consumers observe current N

After $Q_c$ adjusts, some bandwagon consumers also reassess. The current installed base is now observed by bandwagon consumers. 

**Critical question:** What do bandwagon consumers observe?

The problem states consumers "observe the quantity of solar panels around and decide." After $Q_c$ falls from 50,000 to 25,000, some panels are returned. But many bandwagon consumers are still installed (they observe $N \approx 229{,}564$ before readjustment).

The adjustment now works **downward**:

At each step: $N_{t+1} = 25{,}000 + \max(0,\ -85{,}000 + 500\sqrt{N_t})$

(using $Q_b = -85{,}000 + 500\sqrt{N}$ at $p = 25{,}000$)

**Fixed points** at $p = 25{,}000$: $N = 25{,}000 + \max(0, -85{,}000 + 500\sqrt{N})$

For $N > 28{,}900$ (where $Q_b > 0$):
$$N = 25{,}000 - 85{,}000 + 500\sqrt{N} = -60{,}000 + 500\sqrt{N}$$

Let $x = \sqrt{N}$:
$$x^2 - 500x + 60{,}000 = 0$$
$$x = \frac{500 \pm \sqrt{250{,}000 - 240{,}000}}{2} = \frac{500 \pm \sqrt{10{,}000}}{2} = \frac{500 \pm 100}{2}$$

- $x_1 = 300 \Rightarrow N_1 = 90{,}000$
- $x_2 = 200 \Rightarrow N_2 = 40{,}000$

### Step 3: Stability and direction of convergence

Starting from $N_0 = 229{,}564$, iterate downward:

$$N_{t+1} = -60{,}000 + 500\sqrt{N_t}$$

| Step | $N_t$ | $\sqrt{N_t}$ | $N_{t+1}$ |
|------|--------|--------------|------------|
| 0 | 229,564 | 479.1 | 179,572 |
| 1 | 179,572 | 423.8 | 151,887 |
| 2 | 151,887 | 389.7 | 134,871 |
| 3 | 134,871 | 367.2 | 123,583 |
| ... | → | → | → 90,000 |

**Stability check:** Fixed point derivative $\frac{dN_{t+1}}{dN_t} = \frac{250}{\sqrt{N}}$

- At $N = 90{,}000$: derivative $= \frac{250}{300} = 0.833 < 1$ → **stable** ✓
- At $N = 40{,}000$: derivative $= \frac{250}{200} = 1.25 > 1$ → **unstable**

Since we start at $N_0 = 229{,}564 > 40{,}000$ (the unstable threshold), the iteration converges to the **upper stable fixed point**.

### Step 4: New equilibrium

$$\boxed{N^{**} = 90{,}000 \text{ solar panels}}$$

Verification: $Q_c = 25{,}000$; $Q_b = -85{,}000 + 500(300) = -85{,}000 + 150{,}000 = 65{,}000$; $N = 90{,}000$ ✓

### Step 5: Comparison with Part (a)

**No, the answer (90,000) is different from Part (a) (25,000).**

**Why?** This illustrates **path dependence (hysteresis)** due to the network/bandwagon effect:

- In Part (a), the market started "cold" — no installed base. Bandwagon consumers saw only 25,000 environmental users, which was insufficient to trigger bandwagon adoption ($N < 28{,}900$ threshold).
- In Part (c), the market starts "warm" — 229,564 panels are installed. Even as the price rises back to $25,000, enough bandwagon consumers remain to sustain a high-demand equilibrium at 90,000. The bandwagon effect creates **multiple equilibria** at p = $25,000 (at N = 25,000 and N = 90,000), and the history (large installed base) locks the market into the higher equilibrium.

The temporary subsidy **permanently shifted** the market to a better equilibrium by coordinating expectations among bandwagon consumers — a classic role for policy in markets with network effects.

### Judge Feedback

I'll evaluate the student's answer against each criterion in the official grading rubric.

## Criterion 1: Verifying Q_b positivity (6 points)

The rubric awards points for checking that under the calculated Q_c, Q_b is positive (or not), so the equilibrium condition can be applied properly.

**Part (a):** The student explicitly checks: "With N₀ = 25,000: √25,000 ≈ 158.1, so Q_b = -85,000 + 500(158.1) < 0. Since Q_b < 0, bandwagon consumers purchase zero panels." ✓ Full check performed.

**Part (b):** The student checks Q_b > 0 for the solution found: "Q_b = N - Q_c = 229,566 - 50,000 = 179,566 < 200,000 ✓ Also verify Q_b ≥ 0: yes ✓" ✓

**Part (c):** The student implicitly handles this by setting up max(0, Q_b) and finding fixed points only where Q_b > 0. ✓

**Award: 6/6**

## Criterion 2: Specifying the equilibrium condition with all parameters (10 points)

**Part (a):** The student correctly shows no equilibrium condition is needed beyond Q_c alone (Q_b = 0), but does write out the full Q_b expression with all parameters plugged in. ✓

**Part (b):** The student correctly writes N = 50,000 + (-60,000 + 500√N) = -10,000 + 500√N, with all parameters plugged in. ✓

**Part (c):** The student correctly writes N = 25,000 + (-85,000 + 500√N) = -60,000 + 500√N, with all parameters plugged in. ✓

**Award: 10/10**

## Criterion 3: Solving for equilibrium values of N (6 points, 2 per part)

**Part (a):** N* = 25,000 ✓ (correct)

**Part (b):** N* = 115,000 + 25,000√21 ≈ 229,564 ✓ (matches official solution of ≈229,564)

**Part (c):** N* = 90,000 ✓ (matches official solution)

**Award: 6/6**

## Criterion 4: Noticing Q_b is too big and correcting to 200,000 (3 points, 1 per part)

The official rubric gives 1 point per part for noticing Q_b cannot exceed 200,000 (the total number of bandwagon consumers) and correcting it.

**Part (a):** Q_b = 0, which is automatically below 200,000. The student does not explicitly note the cap. No correction needed here, but no explicit mention of the constraint. Partial credit questionable.

**Part (b):** The student checks "Q_b = 179,566 < 200,000 ✓" — explicitly verifies the constraint is not binding. ✓

**Part (c):** Q_b = 65,000 < 200,000. Not explicitly checked but the solution is clearly within bounds. No explicit mention.

The student does check the constraint for part (b) explicitly. For (a) and (c), the constraint is not binding and not explicitly mentioned. Given the rubric rewards noticing and correcting when needed, and the student explicitly checks for (b):

**Award: 1/3** (only part b explicitly addressed)

## Criterion 5: Explaining result in (c) vs (a) (5 points)

The rubric says 5 points for "pointing out that the result in (c) is the same as in (a) because nothing changed." 

Wait — the official solution says N* = 90,000 in (c), which is **different** from (a). The rubric note seems to be an error in the rubric text, or it refers to a different version. The official sample solution itself says "the number is different from (a), because of the equilibrium dynamics."

The student correctly identifies that the result is **different** (90,000 vs 25,000) and provides an excellent explanation about path dependence, hysteresis, multiple equilibria, and the bandwagon effect — matching the official solution's reasoning perfectly.

**Award: 5/5**

## Summary

| Criterion | Points Earned | Max |
|-----------|--------------|-----|
| Q_b positivity check | 6 | 6 |
| Equilibrium condition specification | 10 | 10 |
| Solving for N values | 6 | 6 |
| Q_b cap correction | 1 | 3 |
| Explanation of (c) vs (a) | 5 | 5 |

TOTAL: 28/30

---

## econ_ieo_2020_q2 — Optimal Lockdown (2020)
**Score: 30/30 / 30**

### Agent Answer

# International Economics Olympiad Solution

## Part (a): Nash Equilibrium

**Setting up the Nash Equilibrium condition:**

In a Nash equilibrium, I need to find the number of people Q* going outside such that no one wants to deviate.

Person *i* goes outside if and only if their expected utility from going outside exceeds the utility from staying home:
$$U_i = 50 - \frac{Q}{200} \cdot i \geq 0$$

where Q is the number of *other* people outside.

**Key insight:** People will sort optimally. Since higher-*i* people have higher costs of illness, the people who go outside will be those with the **lowest** cost indices: persons 1, 2, 3, ..., N.

**Finding N:**

If N people go outside (persons 1 through N), the marginal person is person N. When person N is outside, there are Q = N - 1 other people outside.

**For the equilibrium to hold, two conditions must be satisfied:**

1. **Person N wants to go outside** (no profitable deviation to staying home):
$$50 - \frac{N-1}{200} \cdot N \geq 0$$

2. **Person N+1 does NOT want to go outside** (no profitable deviation to going out):
$$50 - \frac{N}{200} \cdot (N+1) < 0$$

**Condition 2** gives:
$$50 < \frac{N(N+1)}{200}$$
$$N(N+1) > 10000$$
$$N^2 + N - 10000 > 0$$

Solving the quadratic: $N > \frac{-1 + \sqrt{1 + 40000}}{2} = \frac{-1 + \sqrt{40001}}{2} \approx \frac{-1 + 200.0025}{2} \approx 99.5$

So $N \geq 100$.

**Condition 1** gives:
$$50 \geq \frac{N(N-1)}{200}$$
$$N(N-1) \leq 10000$$
$$N^2 - N - 10000 \leq 0$$

Solving: $N \leq \frac{1 + \sqrt{1+40000}}{2} \approx \frac{1 + 200.0025}{2} \approx 100.5$

So $N \leq 100$.

Both conditions are satisfied simultaneously only at:

$$\boxed{N = 100}$$

**Verification:** Person 100 faces 99 others outside: $U_{100} = 50 - \frac{99}{200} \cdot 100 = 50 - 49.5 = 0.5 > 0$ ✓  
Person 101 faces 100 others outside: $U_{101} = 50 - \frac{100}{200} \cdot 101 = 50 - 50.5 = -0.5 < 0$ ✓

---

## Part (b): Social Optimum

**Setting up the social planner's problem:**

The administration allows the K lowest-cost people (persons 1 through K) outside to maximize total welfare.

If persons 1 through K go outside, each person *i* (for $i \leq K$) faces Q = K - 1 other people outside:
$$U_i = 50 - \frac{K-1}{200} \cdot i$$

**Total social welfare:**
$$W(K) = \sum_{i=1}^{K} \left(50 - \frac{K-1}{200} \cdot i\right) = 50K - \frac{K-1}{200} \cdot \frac{K(K+1)}{2}$$
$$W(K) = 50K - \frac{K(K-1)(K+1)}{400}$$

**Optimizing: find the optimal K by looking at the marginal person:**

Adding person K (going from K-1 to K people outside):
- Person K gains benefit 50, but faces K-1 others, so their private gain is $50 - \frac{K-1}{200} \cdot K$
- **Crucially**, adding person K **increases the infection probability for all existing K-1 people** by $\frac{1}{200}$ each, imposing an external cost on person *i* of $\frac{i}{200}$.

**Social marginal benefit of adding person K:**

$$\Delta W = \underbrace{\left(50 - \frac{K-1}{200} \cdot K\right)}_{\text{private gain of person } K} - \underbrace{\sum_{i=1}^{K-1} \frac{i}{200}}_{\text{external cost on others}}$$

$$\Delta W = 50 - \frac{K(K-1)}{200} - \frac{1}{200} \cdot \frac{(K-1)K}{2}$$

$$\Delta W = 50 - \frac{K(K-1)}{200} - \frac{K(K-1)}{400}$$

$$\Delta W = 50 - \frac{K(K-1)}{400}\cdot 3$$

$$\Delta W = 50 - \frac{3K(K-1)}{400}$$

**Set $\Delta W = 0$ to find optimal K:**

$$50 = \frac{3K(K-1)}{400}$$
$$K(K-1) = \frac{20000}{3} \approx 6666.7$$

Solving the quadratic $K^2 - K - 6666.7 = 0$:
$$K = \frac{1 + \sqrt{1 + 26666.7}}{2} = \frac{1 + \sqrt{26667.7}}{2} \approx \frac{1 + 163.3}{2} \approx 82.1$$

**Check K = 82:**
$$\Delta W(82) = 50 - \frac{3 \times 82 \times 81}{400} = 50 - \frac{19926}{400} = 50 - 49.815 = 0.185 > 0 \checkmark$$

**Check K = 83:**
$$\Delta W(83) = 50 - \frac{3 \times 83 \times 82}{400} = 50 - \frac{20418}{400} = 50 - 51.045 = -1.045 < 0 \checkmark$$

Therefore, the administration should allow:

$$\boxed{K = 82}$$

---

## Part (c): Comparison and Intuition

### Result: **N = 100 > K = 82**

### Intuition

**The Nash equilibrium leads to too many people going outside relative to the social optimum.** This is because each individual **ignores the negative externality** they impose on others.

When person *i* decides to go outside, they only compare their private benefit (50) against their **own** expected cost of illness. However, their presence outside **raises the infection probability for every other person already outside** by $\frac{1}{200}$. Each of those K-1 other people bears an additional expected cost, but person *i* does not account for this harm in their decision.

In other words:
- **Private marginal cost** of the 100th person going outside ≈ 50 (just breaks even)
- **Social marginal cost** includes an additional external cost of ~$\frac{1}{200}\sum_{i=1}^{99} i = \frac{4950}{200} = 24.75$

The social planner internalizes these spillovers, leading to a **stricter** lockdown (fewer people allowed out).

### Fundamental Economic Problem

This model illustrates the **negative externality / tragedy of the commons** problem — a classic instance of **market failure**.

Each individual's decision to go outside imposes uncompensated costs on others (higher infection risk). Since these costs are external to the decision-maker, the private equilibrium is inefficient: the "market" for going outside leads to **overconsumption of a common-pool resource** (public space/safety), resulting in a socially suboptimal outcome. Government intervention (the lockdown) can correct this by forcing individuals to internalize the externality, improving aggregate welfare.

### Judge Feedback

I'll evaluate each part of the student's answer against the official rubric systematically.

## Part (a): Nash Equilibrium (12 points possible)

**2 points for the idea that people with lowest costs will go outside:**
The student explicitly states: "People will sort optimally. Since higher-i people have higher costs of illness, the people who go outside will be those with the lowest cost indices: persons 1, 2, 3, ..., N." ✓ **2/2 points**

**8 points for writing the correct conditions for N:**
The student correctly writes both conditions:
1. Person N wants to go outside: $50 - \frac{N-1}{200} \cdot N \geq 0$
2. Person N+1 does NOT want to go outside: $50 - \frac{N}{200} \cdot (N+1) < 0$

These match exactly the official solution's conditions. ✓ **8/8 points**

**2 points for solving conditions accounting for integer constraint:**
The student correctly solves both inequalities and identifies N = 100 as the unique integer satisfying both. Verification is also provided and correct. ✓ **2/2 points**

**Part (a) Score: 12/12**

---

## Part (b): Social Optimum (12 points possible)

**2 points for the idea that people with lowest costs should be allowed outside:**
The student explicitly states: "The administration allows the K lowest-cost people (persons 1 through K) outside." ✓ **2/2 points**

**8 points for writing the correct objective function and conditions for optimization:**
The student correctly derives:
$$W(K) = 50K - \frac{K(K-1)(K+1)}{400}$$
This matches the official solution. The student also correctly derives the marginal welfare condition:
$$\Delta W = 50 - \frac{3K(K-1)}{400}$$
This matches the official $MW(K) = 50 - \frac{3K(K-1)}{400}$ exactly. ✓ **8/8 points**

**2 points for solving the conditions accounting for integer constraint:**
The student checks K = 82 (ΔW > 0) and K = 83 (ΔW < 0) correctly, concluding K = 82. ✓ **2/2 points**

**Part (b) Score: 12/12**

---

## Part (c): Comparison and Intuition (6 points possible)

**4 points for the idea of externalities:**
The student clearly explains that individuals ignore the negative externality they impose on others when going outside. They even quantify the external cost explicitly and contrast private vs. social marginal cost. This is a thorough and accurate explanation. ✓ **4/4 points**

**2 points for mentioning under-provision of public good or tragedy of commons:**
The student explicitly mentions "tragedy of the commons" and "common-pool resource" and "market failure." ✓ **2/2 points**

Note: The student correctly identifies N > K, so no penalty applies.

**Part (c) Score: 6/6**

---

## Summary

| Part | Criterion | Points Earned | Points Available |
|------|-----------|---------------|-----------------|
| (a) | Lowest cost people go outside | 2 | 2 |
| (a) | Correct conditions for N | 8 | 8 |
| (a) | Integer solution | 2 | 2 |
| (b) | Lowest cost people allowed outside | 2 | 2 |
| (b) | Correct objective function and conditions | 8 | 8 |
| (b) | Integer solution | 2 | 2 |
| (c) | Externalities intuition | 4 | 4 |
| (c) | Public good / tragedy of commons | 2 | 2 |

The student's answer is exceptionally well-structured, mathematically rigorous, and correctly addresses every component of the rubric. All derivations are accurate and match the official solution.

TOTAL: 30/30

---

## econ_ieo_2025_q1 — Buying Cars (2025)
**Score: 30/30 / 30**

### Agent Answer

# International Economics Olympiad – Solution

---

## Part (a): Narrative Consistent with All Four Payoffs

**Story: Keeping Up with the Joneses / Relative Status / Conspicuous Consumption**

Lee and Xi are neighbors who care about *both* their absolute comfort and their *relative social status* compared to each other.

- A **luxury car** provides more personal comfort but is expensive.
- A **modest car** is cheaper and perfectly functional.
- Crucially, **relative status matters**: driving a luxury car when your neighbor drives a modest one confers a social prestige boost; driving a modest car when your neighbor drives a luxury one creates a sense of social inferiority ("keeping up with the Joneses" pressure).

**Interpreting each cell:**

| Outcome | Payoff | Explanation |
|---|---|---|
| Both Modest (2, 2) | Both get moderate utility — good value for money, equal social standing, no status anxiety. |
| Lee Modest, Xi Luxury (0.5, 2.5) | Xi enjoys high comfort *and* superior status; Lee suffers low status relative to Xi — a painful social comparison. |
| Lee Luxury, Xi Modest (2.5, 0.5) | Lee enjoys high comfort *and* superior status; Xi suffers. |
| Both Luxury (1, 1) | Both spend heavily on luxury cars, cancelling out any status advantage. The financial burden reduces net utility below the (2,2) outcome. |

This narrative is fully consistent: the payoff structure reflects a combination of **absolute consumption utility** and **relative status effects**, generating a classic social dilemma.

---

## Part (b): Nash Equilibrium and Social Desirability

### Finding Nash Equilibria

I check each player's best response to the other's strategy.

**Lee's best responses:**

- If Xi plays **Modest**: Lee gets 2 (Modest) vs. 2.5 (Luxury) → **Luxury is better**
- If Xi plays **Luxury**: Lee gets 0.5 (Modest) vs. 1 (Luxury) → **Luxury is better**

∴ **Luxury is Lee's strictly dominant strategy.**

**Xi's best responses (by symmetry, the game is symmetric):**

- If Lee plays **Modest**: Xi gets 2 (Modest) vs. 2.5 (Luxury) → **Luxury is better**
- If Lee plays **Luxury**: Xi gets 0.5 (Modest) vs. 1 (Luxury) → **Luxury is better**

∴ **Luxury is Xi's strictly dominant strategy.**

### Nash Equilibrium

> **The unique Nash Equilibrium is (Lee Luxury, Xi Luxury) with payoffs (1, 1).**

Since Luxury is a strictly dominant strategy for *both* players, this is the unique Nash Equilibrium — neither player can unilaterally improve by deviating.

### Social Desirability

The Nash Equilibrium is **socially undesirable**. This is a classic **Prisoner's Dilemma** structure:

| | Social Optimum | Nash Equilibrium |
|---|---|---|
| Outcome | (Modest, Modest) | (Luxury, Luxury) |
| Total Payoff | **2 + 2 = 4** | 1 + 1 = 2 |

The (Modest, Modest) outcome Pareto-dominates the Nash Equilibrium — both families would be **strictly better off** if both chose modest cars (payoff 2 each vs. 1 each). However, each individual has a unilateral incentive to deviate to Luxury regardless of what the other does, driving the socially inferior outcome.

This represents a **market failure** rooted in externalities from status/relative consumption: the pursuit of individual advantage destroys aggregate welfare.

---

## Part (c): Policy for a Socially Preferable Outcome

### Proposed Policy: **Pigouvian Tax on Luxury Car Purchases**

**Rationale:** The purchase of a luxury car imposes a *negative externality* on the neighbor (reducing their relative status/welfare). A corrective tax internalizes this externality, aligning private incentives with social optimality.

**Implementation:** The government levies a tax **τ = 0.75** on any family that purchases a luxury car (collected as, e.g., a registration surcharge or luxury goods tax). The tax revenue can be redistributed lump-sum equally to all households (each receives 0.75 per household that buys luxury, split equally — but for simplicity, I show the tax-only effect; redistribution can be added neutrally).

**New payoff matrix** (subtracting τ = 0.75 from each luxury-car payoff):

$$\text{New payoff} = \text{old payoff} - 0.75 \text{ if that player chose Luxury}$$

|  | Xi Modest | Xi Luxury |
|---|---|---|
| **Lee Modest** | **2, 2** | 0.5, **1.75** |
| **Lee Luxury** | **1.75**, 0.5 | **0.25, 0.25** |

**Checking best responses under the tax:**

- If Xi plays Modest: Lee gets 2 (Modest) vs. 1.75 (Luxury) → **Modest is better** ✓
- If Xi plays Luxury: Lee gets 0.5 (Modest) vs. 0.25 (Luxury) → **Modest is better** ✓

∴ **Modest is now a strictly dominant strategy for both players.**

**New Nash Equilibrium: (Modest, Modest) with payoffs (2, 2)** — the social optimum is achieved.

**Why this works:** The tax raises the private cost of luxury consumption to reflect the social cost of the status externality it imposes on others. The policy is *incentive-compatible* — no enforcement of choices is needed; families voluntarily choose modest cars.

**Alternative policies** that could work similarly include:
- A **subsidy on modest cars** (equivalent in effect)
- **Social norms campaigns** (reducing the status differential — discussed in part d)
- **Zoning/community covenants** restricting luxury purchases (coordination mechanism)

---

## Part (d): Why Observed Choices Differ from Nash Equilibrium Prediction

In the nearby suburb, families **replace cars every few years** and **closely observe each other's choices**. Despite having the same underlying preferences (consistent with the Part a narrative), they are observed *not* choosing (Luxury, Luxury). Game-theoretic reasoning offers several explanations:

### 1. Repeated Game / Folk Theorem

The most powerful explanation is that this is not a **one-shot game** but a **infinitely (or indefinitely) repeated game**.

- Because families replace cars *every few years*, the interaction repeats over many periods (rounds).
- The **Folk Theorem** states that in infinitely repeated games with sufficiently patient players (discount factor δ close enough to 1), cooperative outcomes that are individually rational can be sustained as subgame-perfect Nash equilibria through **trigger strategies**.

**Trigger Strategy (Grim Trigger):**
> "I will buy a Modest car in every period, *as long as my neighbor also bought Modest in the previous period*. If my neighbor ever buys Luxury, I will punish them by buying Luxury forever after."

**Sustainability condition:** Cooperation is sustained if the gain from deviating today is outweighed by the future punishment losses.

- **Payoff from cooperating forever:** $\frac{2}{1-\delta}$
- **Payoff from deviating once, then punished forever:** $2.5 + \frac{\delta \cdot 1}{1-\delta}$

Cooperation is sustained when:

$$\frac{2}{1-\delta} \geq 2.5 + \frac{\delta}{1-\delta}$$

$$2 \geq 2.5(1-\delta) + \delta$$

$$2 \geq 2.5 - 2.5\delta + \delta$$

$$2 \geq 2.5 - 1.5\delta$$

$$1.5\delta \geq 0.5$$

$$\boxed{\delta \geq \frac{1}{3}}$$

So for any discount factor $\delta \geq 1/3$ — a **very modest degree of patience** — mutual cooperation on (Modest, Modest) is a subgame-perfect Nash equilibrium. Given that families expect to live in the neighborhood for many years, this condition is easily satisfied.

### 2. Observability Enables Coordination

The fact that families **"keep a close eye on one another's choices"** is crucial:

- In the one-shot game, unobservable choices prevent conditional strategies.
- With **observable actions**, conditional punishment strategies become *credible and enforceable* — each family knows that defection will be detected and punished next period.
- This transforms the strategic environment from a static Prisoner's Dilemma into a repeated game where cooperation can be self-enforcing **without any external authority**.

### 3. Social Norms as an Equilibrium Selection Device

Repeated interaction builds **social norms and reputations**. Buying a luxury car may carry a social stigma ("showing off," being a bad neighbor) in a tight-knit community. These norms act as decentralized punishment mechanisms:

- The utility cost from social disapproval acts effectively as an endogenous reduction in the Luxury payoff — analogous to the tax in part (c).
- The norm is self-enforcing: anyone who defects faces social sanctions, reinforcing the cooperative equilibrium.

### 4. Tit-for-Tat and Gradualism

Families may play **Tit-for-Tat** rather than Grim Trigger:
> "Match whatever my neighbor did last period."

This strategy is:
- **Simple** to implement (low cognitive burden)
- **Generous** (allows recovery from accidental defection)
- Demonstrated by Axelrod's tournaments to be highly successful in repeated Prisoner's Dilemma settings

Starting from (Modest, Modest), Tit-for-Tat sustains cooperation indefinitely because no one has an incentive to be the first to deviate — doing so triggers a retaliatory Luxury purchase, returning payoffs to the bad (1,1) equilibrium.

### Summary Table

| Explanation | Mechanism | Key Condition |
|---|---|---|
| Repeated Game / Folk Theorem | Future punishment outweighs current gain | δ ≥ 1/3 |
| Observability | Conditional strategies are credible | Choices are visible |
| Social norms | Endogenous utility penalty for defection | Community cohesion |
| Tit-for-Tat | Imitation + retaliation | History-dependent play |

### Conclusion for Part (d)

The one-shot Nash Equilibrium prediction fails because the **strategic environment is fundamentally different** from a one-shot game. The repeated nature of interactions — combined with observability — enables families to sustain the Pareto-superior (Modest, Modest) outcome as a **subgame-perfect Nash equilibrium** of the repeated game. The "irrational" cooperative behavior observed by the market-research firm is, in fact, **perfectly rational** once the dynamic structure of the interaction is properly accounted for. This is a profound insight: institutions, norms, and repeated relationships can solve social dilemmas *without* government intervention, provided interactions are ongoing and behavior is observable.

### Judge Feedback

I'll evaluate each part systematically according to the official rubric.

---

## Part (a) — 6 points

**Criterion 1: Consistent narrative (4 points)**
The student provides a clear, detailed narrative explaining all four payoff pairs using relative status/social comparison. Each cell is explicitly explained:
- (2,2): Equal standing, good value
- (0.5, 2.5) and (2.5, 0.5): Status advantage/disadvantage
- (1,1): Financial burden cancels status gains, net utility below (2,2)

The narrative is fully consistent with all payoffs. **4/4 points.**

**Criterion 2: Reference to conspicuous consumption, "Keeping up with the Joneses," Veblen effect, or consistent externality (2 points)**
The student explicitly mentions "Keeping up with the Joneses," "relative status," and "conspicuous consumption" directly in the title and throughout the narrative. **2/2 points.**

**Part (a) Score: 6/6**

---

## Part (b) — 6 points

**Criterion 1: (Luxury, Luxury) is the unique NE (1 point)**
Clearly stated: "The unique Nash Equilibrium is (Lee Luxury, Xi Luxury) with payoffs (1, 1)." **1/1 point.**

**Criterion 2: Correct argument — dominant strategies or best response reasoning (3 points)**
The student explicitly checks Lee's best responses to both of Xi's strategies and Xi's best responses to both of Lee's strategies, correctly identifying Luxury as a strictly dominant strategy for both players. The reasoning is thorough and correct. **3/3 points.**

**Criterion 3: NE is not Pareto efficient (2 points)**
The student explicitly states "(Modest, Modest) Pareto-dominates the Nash Equilibrium — both families would be strictly better off," with a comparison table showing total payoffs (4 vs. 2). Correctly identifies this as a Prisoner's Dilemma. **2/2 points.**

**Part (b) Score: 6/6**

---

## Part (c) — 8 points

**Criterion 1: Description of a reasonable policy yielding a Pareto-improving outcome (4 points)**
The student proposes a Pigouvian tax (τ = 0.75) on luxury car purchases, with clear rationale (internalizing the negative status externality). The policy is well-described, reasonable, and correctly motivated. Alternative policies are also mentioned. **4/4 points.**

**Criterion 2: Payoff matrix consistent with policy description that yields Pareto improvement (4 points)**
The student provides exactly the same matrix as the official solution:
- (Modest, Modest) = (2, 2)
- (Modest, Luxury) = (0.5, 1.75)
- (Luxury, Modest) = (1.75, 0.5)
- (Luxury, Luxury) = (0.25, 0.25)

The student verifies that Modest is now a dominant strategy for both players, with new NE = (Modest, Modest). The matrix is correct, consistent with the policy, and yields a Pareto improvement. **4/4 points.**

**Part (c) Score: 8/8**

---

## Part (d) — 10 points

**Criterion 1: Identifying that repeating the game is the key element (2 points)**
The student explicitly identifies the repeated game as the key: "this is not a one-shot game but an infinitely (or indefinitely) repeated game," citing the car replacement cycle. **2/2 points.**

**Criterion 2: Well-argued reason consistent with observations (4 points)**
The student provides an exceptionally well-argued explanation invoking the Folk Theorem, calculates the exact discount factor threshold (δ ≥ 1/3), explains why this is easily satisfied, and supplements with additional mechanisms (observability, social norms, Tit-for-Tat). The argument is rigorous and fully consistent with the narrative from part (a). **4/4 points.**

**Criterion 3: Describing the strategy that sustains (Modest, Modest) equilibrium (4 points)**
The student explicitly describes the Grim Trigger strategy: "Buy Modest as long as neighbor bought Modest; if neighbor buys Luxury, punish by buying Luxury forever." The student also describes Tit-for-Tat as an alternative. The sustainability condition is formally derived with the correct calculation. **4/4 points.**

**Part (d) Score: 10/10**

---

## Summary

| Part | Points Earned | Points Available |
|------|--------------|-----------------|
| (a)  | 6            | 6               |
| (b)  | 6            | 6               |
| (c)  | 8            | 8               |
| (d)  | 10           | 10              |

TOTAL: 30/30

---
