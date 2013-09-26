=========
Resources
=========

:author: Daniel Lindsley
:status: Draft
:created: 2013/08/06
:updated: 2013/08/06


Goals
=====

Concrete Goals
--------------

* A gentler interface than "Connection"
* More Pythonic

    * This means instance state, as opposed to the all-function-params approach
      of "Connection" instances

* Akin to many of the existing objects in boto2
* Minimal coding on our part to create/maintain these interfaces

Pie-In-The-Sky Goals
--------------------

* Can dynamically adapt to the "Connection" object?
* Sharable information between SDKs?
* Standardized (CRUD-like?) interfaces between different classes?
* Relations between classes for discovery/convenience?


Implementation Requirements
===========================

* Each object will use a subset of the "Connection" object's methods
* Each object will have state to track:

    * Primarily instance variables
    * Either things the user sets or return values from the service

* The data coming out of the "Connection" is leaky:

    * Needs to mangle return data
    * Needs to store known data on the instance
    * Needs to (potentially) initialize other objects
    * Needs to throw proper errors on exceptions/HTTP status codes

* May need to grow additional methods that don't talk to the API
* If it has child (or parent) objects, it needs to know which ones & how to
  build them


Required Info
=============

* Data that should appear on the instance itself

    * Needs to be known ahead of time

* Data to pass to a given method
* Data received from a method

    * What instance variables to set
    * What to log
    * What data to return

* Possible exceptions out of a given method

    * What constitues a retry-able error & not
    * If there's an error message, how do we return/raise it


Issues
======

* How do we standardize this so multiple SDKs can use?

    * JSON

        * This could easily be pronounced YAML instead, but with few gains
        * (Pro) Easily shared
        * (Con) Super-verbose, much longer than the implementations themselves
        * (Con) Poorly suited to logical operations
        * (Con) All the normal issues that come with JSON

    * A DSL is an option

        * (Pro) Shorter & less verbose than JSON
        * (Pro) Better logic than JSON
        * (Con) We risk creating our own Turing-complete language
        * (Con) Each language would need its own parser
        * (Con) Language-specific features will get missed
        * (Con) This is one huge bikeshed to paint

    * Using an intermediate language

        * Think Lua or Lisp, something relatively easy to parse
        * (Pro) Less overhead to implement
        * (Con) We're essentially creating a whole new SDK
        * (Con) Each language would need its own parser
        * (Con) Language-specific features will get missed

    * Implementing as part of the native language(s)

        * Attributes on classes, with tooling to compare the different SDKs
          for differences
        * (Pro) Most "native" approach
        * (Pro) Tools should help spot inconsistencies or things to update
        * (Pro) One SDK can update & the tooling can help the others update
          quickly
        * (Con) More hand-coding/duplication between the SDKs
        * (Con) Need to build the tools that can parse many different langauges
          in a rudimentary way

    * This still doesn't help with "SDK drift"
    * Guaranteed weird-edge cases
    * Doesn't really help with supporting multiple versions of a service
      without duplicating the whole thing
    * YATTLAP - Yet Another Thing To Load And Parse

* CRUD-like interfaces

    * While this sounds nice in theory, the reality is that there's very uneven
      support for this throughout the SDKs.
    * This maps a subset, but not a very useful one
    * Still lots of other methods to write that aren't much different/more
      complex than the CRUD case

        * This is the actual heart of all of this, which is how do we map the
          "right" interface to the underlying "Connection" interface?

    * The only real benefit is standardization

* Method names

    * To be "natural", we've got some painful mangling we're going to have to
      do.
    * Just like below ("data appear on instance"), we have two options:

        * Introspecting has issues with false positives & potentially weird
          method names
        * Static lists work great, but don't work for older versions

* From the "Required Info" section:

    * Data that should appear on the instance itself

        * Options are introspecting (looking for commonalities) or a static list
          of things to watch for

            * Introspecting could be fraught with false positives. For instance,
              ``consistent`` in DDB is in several places, but should be
              operation-level, not instance-level
            * A static list would work well for the common case (using the
              current API version), but would fall down when trying to support
              older versions

    * Data to pass to a given method

        * This gets difficult with conditional data. For example:

            * Exclusive params (pass one or the other but not both)
            * Dependent params (if one is present, another must be supplied)

        * If it's not coming from the instance, we need to setup a parameter
          list the end user needs to supply

    * Data received from a method

        * What gets set on the instance?
        * What if different shapes can come back?
        * How to we tell an error from a successful request?
        * How on earth are we going to mangle the return data the right way?

* Documentation on this is going to be a PITA

    * If we go pure-generative, determining which variables to internally
      document & then building those docs **will** be difficult
    * Similarly, generating external docs won't be much easier
    * Lots of ripping things apart & doing painful text transformations
    * Won't cover how the instance works either

        * ...unless we find a way to template it out. :/


Where We've Been
================

* Tried JSON, but it was too verbose & didn't work well for logic issues
* Started a DSL, but quickly fell down the "don't-want-to-design-a-crappy-language"
  pithole & abandoned


Where To Go From Here
=====================

* The "attributes on classes" approach sounds the most promising at the moment

    * Since it'll for-sure work
    * Gets the SDK functional sooner
    * Tooling can be developed later as we have time

* Documentation is still huge & unsolved
