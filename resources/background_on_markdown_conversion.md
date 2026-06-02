<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# i have a lot of scientific publications (mostly papers, some textbooks) as pdf files on my computer. i want to convert them to proper markdown so handling them with llms becomes easier. I want to convert them locally. What tools or python libraries are available for this? A special thing is that i want to convert formulas to latex. what approaches can be taken?

You can get very good local PDF → Markdown (with LaTeX math) today, but it’s usually a pipeline rather than a single perfect tool. Here are the main libraries/tools and realistic approaches.

## Turnkey PDF → Markdown tools with math support

These try to do everything in one shot: layout, text, tables, and equations.


| Tool | Output | Math handling | Notes |
| :-- | :-- | :-- | :-- |
| Marker | Markdown, JSON, HTML | “Converts most equations to LaTeX” | Optimized for books \& scientific papers, GPU/CPU/MPS. |
| MinerU | Markdown, JSON | Auto-recognizes and converts formulas to LaTeX | Strong focus on scientific literature \& symbol conversion. |
| Nougat | Markdown-like markup | Understands LaTeX math and tables | End‑to‑end academic PDF OCR. |
| Dolphin | Markdown/JSON, HTML | Outputs LaTeX for formulas | Layout‑first, then element parsing. |
| MarkItDown | Markdown | Mostly plain text, weak math semantics | Good “quick and dirty” fallback. |
| Docling | Markdown/HTML | Good structure \& tables, math less central | Designed for structured outputs. |

**Marker (marker-pdf / marker)**

- Marker converts PDFs (and other formats) into Markdown, JSON, chunks, and HTML, with layout, tables, forms, equations, inline math, links, and code blocks preserved.[^1][^2]
- It explicitly “converts most equations to LaTeX” and is optimized for books and scientific papers, working on GPU, CPU, or Apple MPS.[^3][^2][^1]
- Python \& CLI usage (roughly): `pip install marker-pdf` then `marker input.pdf --output out_dir` to get `.md` plus extracted images.[^2][^1]

**MinerU (magic-pdf)**

- MinerU is a document parsing tool that converts PDFs, images, DOCX, PPTX, and XLSX into machine‑readable formats like Markdown and JSON.[^4]
- It was developed specifically for scientific literature pre‑training and supports: removal of headers/footers, correct reading order (multi‑column), preserving headings/lists, extracting images/tables, and automatically recognizing formulas and converting them to LaTeX.[^4]
- It’s installable locally via `pip install -U "magic-pdf[full]"` in a conda env, with CPU/GPU modes; note it’s AGPL‑3, which matters if you integrate it into closed‑source tools.[^5][^4]

**Nougat (Meta AI)**

- Nougat is a Transformer‑based OCR model (“Neural Optical Understanding for Academic Documents”) that takes page images and outputs a lightweight markup language similar to Markdown, including mathematical expressions.[^6][^7]
- The official implementation provides a CLI: `pip install nougat-ocr` then `nougat path/to/file.pdf -o output_directory --markdown` to get markdown‑style output, including LaTeX math and tables.[^8][^6]
- Because it works on rasterized pages, it handles scanned papers and textbooks (not just PDFs with embedded text).[^7][^6]

**Dolphin (ByteDance)**

- Dolphin is a document AI that analyzes PDF layouts first, then parses each element to produce structured Markdown/JSON for text, HTML for tables, and LaTeX for formulas.[^9]
- It explicitly targets complex PDFs with multi‑column layouts and aims to preserve structure for RAG and search pipelines.[^10][^9]

**MarkItDown (Microsoft)**

- MarkItDown is a Python tool from Microsoft that converts many file formats (PDF, Word, PPT, Excel, images, audio) to Markdown; usage is as simple as `markitdown path-to-file.pdf > doc.md` or via a Python API.[^11][^12][^13]
- Reviews and benchmarks note that for PDFs it tends to output flat text with limited table structure and no special handling of equations beyond whatever the underlying OCR sees, so it’s best when you just need text and basic headings.[^14][^15]

**Docling**

- Docling is a library that converts documents into structured Markdown and was evaluated as producing precise Markdown tables with minor post‑corrections in benchmarks.[^15]
- It’s useful if tables and structure are important and you’re prepared to handle math separately.


## Equation‑focused OCR libraries (LaTeX from images)

Even with the best PDF → Markdown tools, equations are where things break. A common pattern is to add a dedicated math OCR model on top.

**pix2tex / LaTeX‑OCR**

- pix2tex (“LaTeX‑OCR”) converts an image of a math formula to LaTeX code using a ViT‑based model.[^16][^17]
- You can install it locally with `pip install pix2tex[gui]` (or the base package) and either use the GUI (`latexocr`) or the Python API to predict LaTeX from in‑memory images.[^17][^16]
- The docs include a `LatexOCR` class and API server for programmatic usage.[^18][^17]

**Pix2Text**

- Pix2Text is an open‑source Python3 tool with small models that recognize layouts, tables, math formulas (LaTeX), and text in images, and convert them into Markdown; it’s pitched as a free alternative to Mathpix.[^19]
- It supports multiple languages, separates layout analysis, table recognition, and text recognition, and outputs Markdown with LaTeX formulas embedded.[^19]

These equation‑OCR tools are especially useful when:

- Your main PDF converter outputs badly rendered equations (e.g., broken Unicode math).
- You’re willing to render PDF pages (or line images) and run a “fallback” math pass.


## Classic PDF parsing libraries for custom pipelines

If you want full control, you can combine lower‑level PDF parsing with your own heuristics and math OCR.

Typical Python options:

- **PyMuPDF (fitz)** or **pypdf** to extract text, bounding boxes, fonts, and render page regions to images.
- **pdfplumber** for structured extraction of text and simple tables.

You’d then:

1. Use a layout/model like Docling, MinerU core, or your own heuristics to identify “equation blocks” (e.g. centered lines, display math, special fonts).
2. Render those regions to images and pass them through pix2tex or Pix2Text to get LaTeX.[^16][^17][^19]
3. Re‑insert LaTeX into your Markdown representation at the right locations.

This is more engineering work, but gives you maximal control and is often the only way to get near‑perfect math for a subset of “problem” papers.

## Practical approaches for your use case

Given you have many scientific PDFs and want local, LLM‑friendly Markdown with LaTeX formulas, I’d think in terms of a tiered pipeline.

### 1. Start with an end‑to‑end PDF → Markdown converter

For batch processing, pick one or two of the modern open‑source pipelines and see how they behave on your corpus:

- **First choice for scientific PDFs with math:**
    - **Marker:** GPU‑accelerated, optimized for books and scientific papers, handles tables and “converts most equations to LaTeX”.[^1][^3][^2]
    - **MinerU:** Strong focus on scientific symbol conversion, preserves structure, auto‑converts formulas to LaTeX; AGPL‑3 but fully local with `magic-pdf`.[^20][^5][^4]
- **Alternative / complementary:**
    - **Nougat:** Particularly good for scanned or camera‑captured papers/textbooks, output already in markdown‑like format with LaTeX math.[^6][^8][^7]
    - **Dolphin:** If you need very careful layout reconstruction and LaTeX formulas and are fine running a larger document AI stack.[^9][^10]
- **For “just give me text” cases or as a fallback:**
    - **MarkItDown** or Docling: simple to integrate, good for raw text or structured tables, but you’d typically combine them with a math OCR step for proper LaTeX equations.[^12][^14][^15][^11]


### 2. Add a math‑cleanup pass for difficult documents

For papers where equations still look wrong after the first pass:

- Render either whole pages or equation bounding boxes to images (via PyMuPDF, `pdftoppm`, etc.).
- Run **pix2tex** or **Pix2Text** on those regions to get LaTeX.[^17][^16][^19]
- Replace the bad equation segments in your Markdown with the LaTeX output (you can wrap inline math in $$ and display math in $$

$$ for later processing).

In practice you can script something like:

- Run MinerU/Marker → `.md` + intermediate layout info.
- Identify blocks tagged as formulas in their JSON/metadata.
- For each such block, re‑OCR with pix2tex or Pix2Text and swap in the LaTeX.


### 3. Use source LaTeX when available

For papers from arXiv and some publishers:

- Download the original TeX source and `pandoc` it to Markdown rather than going through PDF → OCR.
- This gives perfect equations and citations; the PDF pipeline becomes a fallback for non‑TeX‑available material.


### 4. Post‑processing for LLM‑friendliness

Regardless of which converter you use, you’ll typically want to:

- Normalize headings, section breaks, and references (e.g., using a small Python script or an LLM pass).
- Decide how to chunk: per section, per subsection, or fixed token windows, depending on your downstream LLM workflow.
- For textbooks, ensure that figure captions and equations stay close to the surrounding explanatory text when you chunk.

***

If you tell me your hardware (CPU‑only vs GPU, OS) and a couple of representative PDFs (born‑digital vs scanned, math‑heavy vs not), I can suggest a concrete tool chain and some example Python scripts to batch‑convert your library.
<span style="display:none">[^21][^22][^23][^24][^25][^26][^27][^28][^29]</span>

<div align="center">⁂</div>

[^1]: https://pypi.org/project/marker-pdf/

[^2]: https://github.com/datalab-to/marker

[^3]: https://pypi.org/project/marker-pdf/0.3.2/

[^4]: https://github.com/opendatalab/mineru

[^5]: https://discourse.devontechnologies.com/t/the-open-source-project-mineru-is-highly-recommended-as-a-tool-for-pdf-to-markdown/83016

[^6]: https://github.com/facebookresearch/nougat/blob/main/README.md

[^7]: https://syncedreview.com/2023/08/31/meta-ais-nougat-enables-conversion-of-mathematic-expressions-from-pdf-files-to-machine-readable-texts/

[^8]: https://github.com/inuwamobarak/nougat

[^9]: https://www.youtube.com/watch?v=MU24smqPcUY

[^10]: https://everyhub.org/from-pdf-to-markdown-with-dolphin-local-fast-and-actually-honest/

[^11]: https://github.com/mcp/microsoft/markitdown

[^12]: https://github.com/microsoft/markitdown

[^13]: https://dev.to/leapcell/deep-dive-into-microsoft-markitdown-4if5

[^14]: https://jimmysong.io/blog/pdf-to-markdown-open-source-deep-dive/

[^15]: https://www.newtuple.com/post/finance-friendly-ocr-how-docling-dolphin-others-tackle-wall-street-pdfs

[^16]: https://lukas-blecher.github.io/LaTeX-OCR/

[^17]: https://github.com/lukas-blecher/LaTeX-OCR

[^18]: https://pix2tex.readthedocs.io/en/latest/pix2tex.html

[^19]: https://github.com/breezedeus/Pix2Text

[^20]: https://www.youtube.com/watch?v=6319KfkA9Tg

[^21]: https://github.com/cuuupid/cog-marker

[^22]: https://github.com/topics/nougat?l=python\&o=desc\&s=stars

[^23]: https://www.reddit.com/r/LaTeX/comments/1bogk83/nougatlatexocr_installation_and_usage/

[^24]: https://github.com/Hermann-web/pix2tex

[^25]: https://www.reddit.com/r/Rag/comments/1jo6vnb/thoughts_on_mineru_for_pdftomarkdown/

[^26]: https://www.youtube.com/watch?v=gW2hegZZwoQ

[^27]: https://n8n.io/workflows/4808-convert-documents-to-markdown-with-mineru-api-and-gpt-4o-mini/

[^28]: https://jimmysong.io/zh/blog/pdf-to-markdown-open-source-deep-dive/

[^29]: https://github.com/microsoft/markitdown/releases

