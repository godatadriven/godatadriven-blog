Title: Production Ready Data Science
Date: 2016-08-24 23:00
Slug: production-ready-ds
Author: Giovanni Lanzani
Excerpt:
Status: draft
Template: article
Latex:

Becoming a data-driven organization is not an easy task. Off the top of my head, and in no
particular order, these are the most frequent challenges a company faces

1. Attracting, retaining, and training the right talents;
2. Making data available cross-silos;
3. Modernize their tech stack or increase the complexity of the IT landscape by adding new
   technologies;
4. Fear of the unknown i.e. many people are afraid about losing control, or their job, to data and
   data science;
5. Lack of vision[^1].

As I was thinking about this list, however, I felt there was something deeper about the troubles
some companies are facing. I know in fact about companies that have made significant progress in
all five points, but that are still not reaping the fruits they were expecting. When I looked at
these companies more closely, they were not putting the models they developed into production. The
reason varied, from being content with report-driven decision making (either a one-off report, or
periodic reporting) to simply struggling with all the pieces of the puzzle.

Being the curious type, I set out to investigate what was making the puzzle so difficult for them.
Productionizing a model involves a series of (moving) pieces:

+ The data should be automatically available for the model, i.e. there should be no[^2] human
  intervention in the ETL phase;
+ The model should also run automatically, follow the DRY principles, should be (battle) tested,
  and possibly be flexible in its sources/sinks, either by being used as a library, or by exposing
  accessible APIs (REST being one the most in vogue today);
+ Refreshing and/or re-training the model should not impact the front-end accessing it, or, in the
  easiest cases, should not impact it during business hours[^3].

The companies struggling with becoming data driven, are also failing in on or more of the above
points. What they are doing is a mix of the following[^4]:

+ They copy the data around manually; this makes it basically impossible to bring a model into
  production because, if the data does not flow automatically, the owner of the data (wherever they
  might be) are probably not even aware that their data is used in a model. If the data comes in
  automatically, instead, the data owner is probably aware that systems are tapping into her data
  and you get almost immediate alerts if the ingestion fails (if not: set it up);
+ They don't test the code so software engineers basically refuse to touch the code; this problem
  is exacerbated when the engineers *have* to re-write the code because of performance or other
  reasons; with tests unavailable, modifying the model becomes daunting;
+ Related to the previous point, data scientists tend to write unreadable or very complicated code;
  this is a consequence of exploration driven modelling: you start poking around the data
  until it suddenly make sense but you leave around all the steps you took, even the unused ones;
  coupling this to a lack of documentation, you can easily end up with thousands of lines of code
  that are basically acting as a scarecrow for your engineers;
+ Sometimes your data scientists code in a language that doesn't nicely operate with the outside
  world; if you're in charge, make this stop as there are no solutions other than complete lock-in.

If you've payed attention to these points, you probably start seeing a pattern, that is: data
scientists usually suck at software quality, that is[^5]: reliability, usability, efficiency,
portability, and maintainability. Because data-driven models are implemented through software, they
suffer from bad software quality just as much as your typical application.

Let me be clear: this is not an easy task! To create a (great) model you need creativity, a
scientific attitude, knowledge of various modeling techniques, etc. Getting data scientists able to
create these models is one of the biggest challenges for an organization. But focusing on the first
three at the cost of software quality, will produce something great and admirable that ends up not
being used.

This is the reason we actively hire data scientists that can code, and can do
[it well](https://www.godatadriven.com/job-data-scientist).

I imagine you now have the next burning question which is: what if the data scientists working at
my organization are not good at it? What if someone left the company, implemented a great new
method, but nobody can actually make sense of what she wrote?

This is where I pitch you our services: training and consultancy. We can train your data scientists
to write code of higher quality and we can review the code they wrote.
[Get in touch.](mailto:signal@godatadriven.com)

[^1]: A lack of vision is a much broader issue than 1-4 as it can bring even the largest and most
  flourishing corporations to the ground (a great read about this is
  [Good to Great](https://en.wikipedia.org/wiki/Good_to_Great)). I included it nonetheless as it
  will cut or make budget unavailable or prevent management buy-in of data-driven products. And
  lack of management buy-in is even worse that lack of budget. One of our first clients installed
  its first Hadoop cluster on dismissed machines, built a type-ahead and recommendation engine for
  their web shop, and see profits surge right after they put it into production. There was nothing
  a budget could do had management not agreed about "letting" the model into production.
[^2]: Unless something breaks of course.
[^3]: Whatever that means for you.
[^4]: This is probably one of the post with the highest density of bullet points I've ever written.
  Apologies.
[^5]: This is a subset of the [ISO 9126](https://en.wikipedia.org/wiki/ISO/IEC_9126) standard on
  software quality.
