Title: Using Kendall's tau to compare recommendations
Date: 2016-07-14 15:00
Slug: kendall-tau-recommendations
Author: Rogier van der Geer
Excerpt: How to use Kendall's tau to compare recommendations.
Template: article
Latex:

<span class="lead">Kendall's tau is a rank correlation metric, used to compare the order of two lists.</span>

### Intro

The [Kendall tau](https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient) is a metric that can be used to compare the order of two ranks. It takes two ranks _that contain the same elements_ and calculates the correlation between them. A correlation of $+1$ means the ranks are equal, while a correlation of $-1$ means the ranks are exactly eachother's reverse. If two ranks are independent or randomly shuffled the correlation will be zero on average.

The Kendall tau is undefined when the two ranks do not contain exactly the same elements. So when one wants to compare
ranks which do not necessarily contain the same elements one needs to look elsewhere. The same goes for comparing only
parts (for example 10 highest entries) of ranks, as these will not likely contain the same elements. An example of this
is when comparing algorithms that provide recommendations: the pool of items is the same for each algorithm, but
we are usually only interested in the best few (let's say top-5) recommendations.

Below I'll explain how you can use a few tricks to make Kendall's tau fit for comparing ranks which do not necessarily
contain the same items. But first let's have a look at the Kendall tau itself.

### Definition

The most used definition of the Kendall tau between two ranks $a$ and $b$ is:

$$\tau \equiv \frac{n_c - n_d}{\sqrt{(n_0-n_a)(n_0-n_b)}},$$

where $n_c$ and $n_d$ are the number of _concordant_ pairs and the number of _discordant_ pairs respectively,
$n_0$ is defined as
$$n_0 \equiv \frac{n(n-1)}{2},$$
where $n$ is the length of the ranks, and $n_a$ and $n_b$ account for ties in the ranks, and are defined as
$$\begin{align}
n_a &\equiv \sum_i \frac{t^a_i (t^a_i-1)}{2},\\\\
n_b &\equiv \sum_j \frac{t^b_j (t^b_j-1)}{2},
\end{align}$$
where $t^a_i$ and $t^b_j$ are the number of ties items in the $i^\text{th}$ group of ties in rank $a$, 
 and the number of ties items in the $j\text{th}$ group of ties in rank $b$ respectively. 

Between the ranks $a$ and $b$, a pair of items $x$ and $y$ is

- _concordant_ if $a_x > a_y$ and $b_x > b_y$, or $a_x < a_y$ and $b_x < b_y$,
- _discordant_ If $a_x > a_y$ and $b_x < b_y$ or vice versa.
- neither _concordant_ nor _discordant_ in the case of ties, if $a_x = a_y$ or $b_x = b_y$.

#### An example

Let's have a look at these two ranks:
```python
rank_a = {'apple': 0, 'banana': 2, 'kiwi': 3, 'pear': 1}
rank_b = {'apple': 2, 'banana': 1, 'kiwi': 3, 'pear': 0}
```


Here $a_\text{apple} < a_\text{pear}$, while $b_\text{apple} > b_\text{pear}$, so this pair is _discordant_. 
Also, $a_\text{pear} < a_\text{banana}$ and $b_\text{pear} < b_\text{banana}$, so that pair is _condordant_.
In total, this example contains four concordant pairs and two discordant pairs. Since $n=4$, this means that
$$\tau = \frac{4-2}{4(4-1)/2} = \frac{1}{3},$$
which means the two ranks are slightly correlated.

Since there are no ties in the above example, we can directly translate it to two lists:
```python
a = ['apple', 'pear', 'banana', 'kiwi']
b = ['pear', 'banana', 'apple', 'kiwi']
```
In list-form, a concordant pair has the same order in both lists, while the order of a discordant pair is swapped between
the lists. Two elements cannot occupy the same spot, so we can not have ties.

### Dealing with mismatches

The definition of the Kendall tau cannot handle items which occur in only one of the lists. But when we are
comparing the top-5 results from recommender $a$ with the top-5 results from recommender $b$ we can expect
to have mismatches: it is unlikely that the algorithms will produce the same results. Nevertheless, we do not
want to compare the entire ranks produced by the recommenders, as we are not at all interested in the bottom of the
rank.

#### Ignoring mismatches

The easiest way to deal with mismatches is to ignore them. By simply removing all elements that do not occur in both
lists we reduce the problem to one that we _can_ solve. For example,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'pineapple']
b = ['pear', 'orange', 'banana', 'apple', 'kiwi']
```
would be reduced to the example above, where $\tau = \frac{1}{3}$. At first glance, that seems acceptable. However, in here:
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'pineapple']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
lists `a` and `b` would be reduced to identical lists, yielding $\tau = 1$ even though the original lists are not the same.

The problems become worse when there are more mismatches in the list:
```python
a = ['pineapple', 'lemon', 'apple', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
would _also_ evaluate to $\tau = 1$ (since `apple` and `kiwi` are concordant), while I would argue the lists are far from
equal. In the extreme case that there is only one match,
```python
a = ['pineapple', 'lemon', 'apple', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'plum', 'orange']
```
the Kendall tau is undefined, as the denominator $n(n-1)/2 = 0$ for $n=1$. So clearly, ignoring mismatches is not the solution to our problem.

#### Appending mismatches

Instead of ignoring the mismatches, we can also append them to the bottom of the other list. In a way this makes sense, since all results _are_ in both lists, just not necessarily in the top-5. Since we do not have any information on _where_
the results are in the list (below the top-5) we should treat all results below the top-5 as equal. For example:
```python
a = ['pineapple', 'apple', 'pear', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
would then become
```python
rank_a = {'apple': 1, 'banana': 5, 'grape': 4, 'orange': 5, 'pear': 2, 'pineapple': 0, 'kiwi': 3}
rank_b = {'apple': 0, 'banana': 2, 'grape': 5, 'orange': 4, 'pear': 1, 'pineapple': 5, 'kiwi': 3}
```
where `banana` and `orange` end up in a tied 5th place in rank `a`, and `pineapple` and `grape` share a tied 5th place
in rank `b`. This yields $\tau = 0.15$, which is close to what I would expect.

If we do this for other examples we get some nice results. For example if only the _last_ element of list `b` is replaced by one that is not in `a`,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
we find $\tau = 0.87$. If instead we change the _first_ element,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
b = ['orange', 'pear', 'banana', 'kiwi', 'grape']
```
we find $\tau = -0.20$ which is much lower, as we expect. Also, if we replace an additional element,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
b = ['orange', 'pear', 'pineapple', 'kiwi', 'grape']
```
we again find a lower correlation: $\tau = -0.45$. 

We encounter a problem if we replace _all_ elements:
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
b = ['orange', 'tomato', 'pineapple', 'lemon', 'plum']
```
where we find a largely negative correlation: $\tau = -0.71$. 
In principle a strongly negative correlation is what we expect 
here, but if we compare this with
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
c = ['grape', 'kiwi', 'banana', 'pear', 'apple']
```
which results in a correlation of $\tau = -1$, I would say this is _not_ what we expect: I would say an inverted top-5 
is closer to the original than one that is completely different.

So why is the correlation of `a` and `b` larger than that of `a` and `c`? It is clear that between `a` and `c` all
pairs of words are discordant. If we have a closer look at the resulting ranks when we compare `a` and `b`:
```python
rank_a = {'apple': 0, 'banana': 2, 'grape': 4, 'kiwi': 3, 'lemon': 5, 
          'orange': 5, 'pear': 1, 'pineapple': 5, 'plum': 5, 'tomato': 5}
rank_b = {'apple': 5, 'banana': 5, 'grape': 5, 'kiwi': 5, 'lemon': 3, 
          'orange': 0, 'pear': 5, 'pineapple': 2, 'plum': 4, 'tomato': 1}        
```
we see that also here there are no concordant pairs. Not all pairs are discordant, however, as all pairs of which both 
items occur in the same list are tied in the rank of the other. For example `apple` and `banana` are tied in rank `b`, 
and are therefore not discordant. So the difference between the two correlations comes from the difference in number 
of ties, or the difference in length of the ranks.

#### Extending the ranks

We can fix the inbalance in number of ties by adding a number of dummy items to the ranks, such that all ranks have the
same length. The ranks we obtain when we compare two lists can never be longer than twice the length of a list,
which is the case then the lists have no common elements. Therefore, if we extend all ranks to twice the length of a list,
every rank will have the same length. 

In the example of `a` and `b` above the lists share no common items and the ranks are twice the length of the lists. 
Therefore we will not add any dummy items, and the correlation will remain $\tau = -0.71$. In the case of `a` and `c`,
however, all items are common, and therefore the ranks have the same length as the lists. We will thus extend the ranks
with dummy items (let's take grains): 
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
c = ['grape', 'kiwi', 'banana', 'pear', 'apple']

rank_a = {'apple': 0, 'banana': 2, 'grape': 4, 'kiwi': 3,  'pear': 1,
          'wheat': 5, 'barley': 5, 'rice': 5, 'corn': 5, 'rye': 5}
rank_c = {'apple': 4, 'banana': 2, 'grape': 0, 'kiwi': 1,  'pear': 3,
          'wheat': 5, 'barley': 5, 'rice': 5, 'corn': 5, 'rye': 5}     
```
which yields a correlation of $\tau = 0.45$. 

Now isn't that a rather high correlation between a list and its inverse? For just these lists that is a 
rather high correlation indeed, but remember that we are comparing the top-5 highest ranked items of (much) longer
lists. The fact that the lists have the same items in their five highest entries makes them fairly similar in my
opinion.

Now let's have a look at a few examples:
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
extended_tau(a, a) -> 1

# replace the last element
b = ['apple', 'pear', 'banana', 'kiwi', 'lemon']
extended_tau(a, b) -> 0.83

# invert
c = ['grape', 'kiwi', 'banana', 'pear', 'apple']
extended_tau(a, c) -> 0.43

# replace the first element
d = ['tomato', 'pear', 'banana', 'kiwi', 'grape']
extended_tau(a, d) -> 0.37

# replace three elements and add three new
e = ['lemon', 'tomato', 'apple', 'pineapple', 'grape']
extended_tau(a, e) -> -0.23

# replace all elements
f = ['orange', 'tomato', 'pineapple', 'lemon', 'plum']
extended_tau(a, f) -> -0.71
```
These results look right: every move to scramble the list even more results in a lower correlation. Replacing the first
element has more impact than replacing the last, and inverting the list results in a far greater correlation than
replacing all elements. The only problem now is the scale: we expect the correlation to scale in the range $[-1, +1]$, but
in this case the minimum value lies around $-0.71$. This minimum value depends on the length of the lists we compare.

#### Scaling the result

We can calculate the minimum value as a function of the length of our lists. Going back to the definition
