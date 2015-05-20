Title: Distance calculation with Impala (or Hive)
Date: 2015-02-05 11:00
Slug: impala-haversine
Author: Alexander Bij
Excerpt: With Impala you can calculate the distance between two geo-points using the Haversine formula.
Template: article
Latex:

### Haversine

The haversine formula is an equation important in navigation, giving great-circle distances between two points on a sphere from their longitudes and latitudes.
It is a special case of a more general formula in spherical trigonometry, the law of haversines, relating the sides and angles of spherical triangles.
The first table of haversines in English was published by James Andrew in 1805. Florian Cajori credits an earlier use by Jose de Mendoza y Ríos in 1801 The term haversine was coined in 1835 by Prof  James Inman.

- Source: [wikipedia-haversine](http://en.wikipedia.org/wiki/Haversine_formula)

My colleague Giovanni described the formula in a [previous post](../the-performance-impact-of-vectorized-operations.html) and coded an implementation in Python with NumPy for fast results.
In this post I show you how to use Impala
 
> This also works in **Hive**. *(but that is way slower ofcourse)*

### Impala query language

Impala has a lot of Math, String, Date and other functions you should [checkout](http://www.cloudera.com/content/cloudera/en/documentation/core/latest/topics/impala_functions.html).
Impala supports all the math functions which are required to implement the formula.
The query I put together:

	:::sql
	select
	  2 * asin(
        sqrt(
          cos(radians(lat1)) *
          cos(radians(lat2)) *
          pow(sin(radians((lon1 - lon2)/2)), 2)
              +
          pow(sin(radians((lat1 - lat2)/2)), 2)
    
        )
      ) * 6371 distance_km
    from my_table;
    

> note: for miles use, 3956 instead of 6371.

### Test

I created an example using Hoofddorp Station to Amsterdam Central Station. In HUE you can plot your query results with lat/lon values on the map.
I assume you may not be familiar where Amsterdam is, but Hoofddorp is well known for it's..., well now you know where Hoofddorp and Amsterdam are located.

- Hoofddorp Station:	52.2909264998,	4.700868765513
- Amsterdam Station:	52.3773759354,	4.896747677825

![both-locations](static/images/impala-haversine/both-locations.png)

Let's use these variables in the query:

	:::sql
	select
	  2 * asin(
        sqrt(
          cos(radians(52.2909264998)) *
          cos(radians(52.3773759354)) *
          pow(sin(radians((4.700868765513 - 4.896747677825)/2)), 2)
              +
          pow(sin(radians((52.2909264998 - 52.3773759354)/2)), 2)
        )
      ) * 6371 distance_km;
    
    -- result: 16.415929129056497

### Verify the result

Using the [google-maps-calculate-distance](https://support.google.com/maps/answer/1628031?hl=en) you can measure the distance between two points on the map.

![google-measurement](static/images/impala-haversine/google-measurement.png)

That's good! Feel free to copy past the formula and use it in Impala or Hive to crunch some geo data.

Greetings, Alexander Bij
