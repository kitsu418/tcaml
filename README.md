# TCaml: Verify the Asymptotic Time Complexity of Simple Programs

<div align=center>
<img src="images/tcaml-logo.svg" width=283>
</div>

## Overview

TCaml is the course project of [CS 560: Reasoning About Programs](https://www.cs.purdue.edu/homes/bendy/cs560/fall25/).

Ensuring that program performs efficiently is an important aspect of algorithm design and software engineering. While verifying that a program produces the right answer has seen significant advancements through automated theorem proving and type systems, verifying non-functional properties such as time complexity remains very challenging. In critical systems, performance guarantees are not only an optimization concern but a correctness requirement. Unexpected exponential blowups can lead to Denial-of-Service (DoS) vulnerabilities or system failures in real-time environments.

The high-level problem we tackle in this project is the automated verification of asymptotic time complexity for recursive programs. Specifically, we address the gap between manual mathematical analysis and fully automated inference tools.

Currently, developers who wish to formally verify the complexity of their code often face a dilemma. They must either use fully automated tools like [Facebook Infer](https://fbinfer.com/docs/checker-cost), which rely on abstract interpretation and may fail to capture complex mathematical dependencies, or use rigid resource-aware type systems (like [TiML](https://dl.acm.org/doi/10.1145/3133903)) that require the user to manually annotate exact cost formulas (e.g., $3n + 2$). The latter places a heavy burden on the programmer to calculate precise constants that are often irrelevant to the asymptotic behavior (Big-O) of the algorithm.

Our goal is to develop a middle-ground approach: a verification framework that allows users to specify a high-level asymptotic complexity claim (e.g., $O(n^2)$), and automatically synthesizes the necessary mathematical proof to validate this claim. By treating complexity verification as a template synthesis problem backed by SMT solvers, we aim to provide a rigorous yet flexible method for proving that a program’s execution cost stays within a specified upper bound.

## Test on examples using Docker

```bash
git clone https://github.com/kitsu418/tcaml.git && cd tcaml
docker build -t tcaml .
docker run -v "$PWD":/workspace --rm tcaml
```

The desired result should be like this:

```
Processing 9 file(s)...

Processing binary-exponentiation.ml... ✓ (0.212s)
Processing binary-search-list.ml... ERROR: Verification failed: Multiple input sizes is not supported.
Processing binary-search.ml... ✓ (0.361s)
Processing factorial.ml... ✓ (0.091s)
Processing fib-exp.ml... ✓ (0.136s)
Processing fib-n-square.ml... ✗ (0.150s)
Processing insertion-sort.ml... ✓ (0.135s)
Processing merge-sort-n.ml... ✗ (0.174s)
Processing merge-sort-nlogn.ml... ✓ (0.364s)

============================================================
SUMMARY
============================================================
Files processed: 6/9
  ✓ Successful: 6
  ✗ Failed: 3

Timing:
  Total time: 1.624s
  Average time per file: 0.271s
  Parse time: 0.438s (27.0%)
  VC generation time: 0.349s (21.5%)
  Verification time: 0.836s (51.5%)

Analysis Results:
  Total functions analyzed: 16
  Total execution paths generated: 47
  Total function calls across all paths: 25
  Average paths per function: 2.94
  Average calls per function: 1.56

Failed files:
  - binary-search-list.ml: Verification failed: Multiple input sizes is not supported.
  - fib-n-square.ml: Verification failed
  - merge-sort-n.ml: Verification failed

Detailed results saved to /workspace/benchmark_results.json
```