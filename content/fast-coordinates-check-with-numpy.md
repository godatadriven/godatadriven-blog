Title: Fast distance checks using numpy
Date: 2014-02-28 15:00
Slug: fast-coordinates-check-with-numpy
Author: Giovanni Lanzani
Excerpt: Checking whether two points are within a certain distance, given their latitude and longitude, is a task that can be accomplished quite quickly by all modern computers. But what if you repeat that operation hundred of thousands of times?  In a C-world, that would also be very fast. In the scripting languages so common nowadays to develop everything from quick shells scripts to web applications, that does not come for free. In this blog post I present how to make it fast with Python.
Template: article
Latex:

Checking whether two points are within a certain distance, given their latitude
and longitude, is a task that can be accomplished quite quickly by all modern
computers. But what if you repeat that operation hundred of thousands of times?
In a C-world, that would also be very fast. In the scripting languages so
common nowadays to develop everything from quick shells scripts to web
applications, that does not come for free. In this blog post I present how to
make it fast with Python.

### First things first: distance between two points

As it would not make sense to improve the performance of a formula without
knowing the formula, let me introduce you with the [Haversine formula][haversine]:

$$
d = 2 r \arcsin\left(\sqrt{\sin^2\left(\frac{\phi_2 - \phi_1}{2}\right) + \cos(\phi_1) \cos(\phi_2)\sin^2\left(\frac{\lambda_2 - \lambda_1}{2}\right)}\right)
$$

where $\phi_{1,2}$ is the latitude of the two points and $\lambda_{1,2}$ is
their longitude (both in [radians]). If you fill in for $r$ the earth (average)
radius, you will get the distance between the two points in the same unit (so
in $km$ if you used $km$, $m$ if you used $m$, and so forth.).

### A pythonic haversine formula

If you're scared by math but in love with Python fear not: we also present you
with the ready to use Python code:

    :::python
    from numpy import sin, cos, pi, arcsin, sqrt
    def get_distance(lat, lon, pcode_lat, pcode_lon):
        """
        Find the distance between `(lat,lon)` and the reference point
        `(pcode_lat,pcode_lon)`.
        """
        RAD_FACTOR = math.pi / 180.0  # degrees to radians for trig functions
        lat_in_rad = lat * RAD_FACTOR
        lon_in_rad = lon * RAD_FACTOR
        pcode_lat_in_rad = pcode_lat * RAD_FACTOR
        pcode_lon_in_rad = pcode_lon * RAD_FACTOR
        delta_lon = lon_in_rad - pcode_lon_in_rad
        delta_lat = lat_in_rad - pcode_lat_in_rad
        # Next two lines is the Haversine formula
        inverse_angle = (sin(delta_lat / 2) ** 2 + cos(pcode_lat_in_rad) *
                         cos(lat_in_rad) * sin(delta_lon / 2) ** 2)
        haversine_angle = 2 * arcsin(sqrt(inverse_angle))
        EARTH_RADIUS = 6367  # kilometers
        return haversine_angle * EARTH_RADIUS

We could ask ourselves how fast this code is when we want to check
400000 postal codes (which is, approximately, the number of postal codes in the
Netherlands). This is useful is we want to get a list of postal codes that fall
within a certain radius from a reference postal code.

### Some performance measurements

To measure the performance of the above code we create an array containing some
random latitude and longitude pairs centered around `(52.3905927,4.8412508)`
which is the coordinate pair of [our office][contact].

    :::python
    from numpy import random
    godatadriven = (52.3905927,4.8412508)
    points = random.randn(400000, 2) * 0.01
    points[:, 0] = points[:, 0] + godatadriven[0]
    points[:, 1] = points[:, 1] + godatadriven[1]

The `points[:, 0]` syntax is the
[NumPy] way of saying: select all fields from the first column, which in
our case would be the latitude of `points`. To measure how much time is needed to get
the distances between `points` and `godatadriven`, we can use [ipython]
`%timeit` magic function, that measures how much time, averaged on multiple
runs, a script takes to execute.

    :::python
    def iterate_distance():
        d = []
        for p in points:
            d.append(get_distance(p[0], p[1], reference[0], reference[1]))
    %timeit iterate_distance()  # result is 3.53 seconds

If you're familiar with Python, the code above will give you the shivers, as it
does not use [list comprehension][list-comprehension]. Changing the code, alas,
only marginally affects performance:

    :::python
    %timeit [get_distance(p[0], p[1], reference[0], reference[1]) for p in points]
    # result is 3.46 seconds

If you're building a real-time application, where a postal code check could be an
intermediate computation, $3$.54s is an eternity. Luckily, we can do some magic
with NumPy.

### Vectorization to the rescue

In our code, `points` is a NumPy array. NumPy arrays can be easily manipulated
because, under the hood, they have been coded to be a really convenient way to
describe blocks of computer memory. The particular structure chosen by NumPy
allows its arrays to be straightforwardly modified by C code. This is
fundamental here because, as we saw above, computing a similar operation 400000
times in Python is not exactly the most clever idea.

Vectorization is a process by which these element-wise operations are grouped
together, allowing NumPy to perform them much more rapidly. In
the code above, you already saw a couple of examples of vectorized operations:

    :::python
    points = random.randn(400000, 2) * 0.01
    points[:, 0] = points[:, 0] + godatadriven[0]

Scaling `randn` by 0.01 didn't require two for-loop for each of its elements:
we simply told NumPy to multiply the whole array by 0.01 and it was done. The
same when we added `godatadriven[0]` to `points[:, 0]`: we didn't have to write
a for-loop for each element because once again NumPy took care of it.

That said, here's the vectorized operation of getting the distance in NumPy:

    :::python
    %timeit get_distance(points[:, 0], points[:, 1], reference[0], reference[1])
    # runs in 21.5 ms!

which is some 165 times faster!

### Putting it all together with Pandas

Now suppose you have a [pandas] dataframe with the complete list of postal
codes

    :::python
    import pandas as pd
    zip = pd.read_csv("zip.csv", names=["zip", "lat", "lon"], index = "zip")

and that, given a postal code and a given radius, you want a list of postal
codes that fall within the given radius. That can be accomplished with the
following code

    :::python
    def get_zips(postal_code, radius):
        """
        Return the postal code that are within `radius` of `postal_code`.
        """
        lat, lon = zip.ix[postal_code]
        zip_distance = get_distance(zip.lat, zip.lon, lat, lon) < radius
        return zip[zip_distance].index.values

Thanks to the vectorized nature of NumPy operations (including the comparison
with `radius` on the previous chunck of code), the check is done in a matter of
milliseconds, making it a good fit for real time web applications.

Note: if you are so inclined, a IPython notebook with the performance test is
online at [nbviewer]. The times reported there may vary slightly compared with
the ones in this post.



[haversine]: http://en.wikipedia.org/wiki/Haversine_formula
[radians]: http://en.wikipedia.org/wiki/Radian
[contact]: http://www.godatadriven.com/contact.html
[NumPy]: http://www.numpy.org
[ipython]: http://www.ipython.org
[list-comprehension]: http://docs.python.org/2/tutorial/datastructures.html#list-comprehensions
[pandas]: http://pandas.pydata.org
[nbviewer]: http://nbviewer.ipython.org/gist/gglanzani/9271842
