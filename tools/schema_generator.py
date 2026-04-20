"""Schema generator — deterministic JSON-LD templates + JSX invocations for Sourcy.

Generates schema.org structured data in two formats:
1. Raw JSON-LD (for validation + embedding in <script> tags)
2. JSX invocations using the existing StructuredData.tsx component API

No LLM required — pure templating based on page metadata inputs.
All tools return JSON strings matching the project's @function_tool pattern.

StructuredData.tsx components (all already exist in the Next.js app):
  OrganizationLD, WebSiteLD, ArticleLD, ProductLD, BreadcrumbLD,
  FAQPageLD, ServiceLD, CollectionPageLD, WebPageLD
"""

import json
from agents import function_tool


# ─── FAQPage Schema ───────────────────────────────────────────────────────────

@function_tool
def generate_faq_schema(
    faqs_json: str,
    page_url: str = "",
) -> str:
    """Generate FAQPage JSON-LD schema and JSX invocation for a set of FAQ items.

    Args:
        faqs_json: JSON array of FAQ objects with 'question' and 'answer' keys.
                   Example: '[{"question": "What is Sourcy?", "answer": "Sourcy is..."}]'
        page_url: Page URL (optional, for context)
    """
    try:
        faqs = json.loads(faqs_json)
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps({"error": f"Invalid faqs_json: {str(e)}"})

    if not isinstance(faqs, list) or not faqs:
        return json.dumps({"error": "faqs_json must be a non-empty JSON array"})

    # Validate each FAQ has required fields
    cleaned_faqs = []
    for i, faq in enumerate(faqs):
        if not isinstance(faq, dict):
            return json.dumps({"error": f"FAQ item {i} must be an object"})
        q = faq.get("question", "").strip()
        a = faq.get("answer", "").strip()
        if not q or not a:
            return json.dumps({"error": f"FAQ item {i} missing 'question' or 'answer'"})
        cleaned_faqs.append({"question": q, "answer": a})

    # JSON-LD
    json_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"],
                },
            }
            for faq in cleaned_faqs
        ],
    }

    # JSX invocation using existing FAQPageLD component
    faqs_prop = json.dumps(cleaned_faqs, indent=2)
    jsx = f'<FAQPageLD faqs={{{faqs_prop}}} />'
    jsx_import = 'import { FAQPageLD } from "@/components/seo/StructuredData";'

    # HTML script tag embedding
    script_tag = (
        '<script type="application/ld+json">\n'
        + json.dumps(json_ld, indent=2)
        + '\n</script>'
    )

    return json.dumps({
        "schema_type": "FAQPage",
        "page_url": page_url,
        "faq_count": len(cleaned_faqs),
        "json_ld": json_ld,
        "script_tag": script_tag,
        "jsx_invocation": jsx,
        "jsx_import": jsx_import,
        "validation_url": "https://validator.schema.org/",
        "instructions": (
            "1. Add the import to the top of the page component.\n"
            "2. Place <FAQPageLD /> inside the page JSX (alongside other schema components).\n"
            "3. For Builder.io blogs: add via Builder.io custom code block."
        ),
    })


# ─── Article Schema ───────────────────────────────────────────────────────────

@function_tool
def generate_article_schema(
    headline: str,
    date_published: str,
    description: str = "",
    author: str = "Sourcy Team",
    url: str = "",
    image: str = "",
    date_modified: str = "",
) -> str:
    """Generate Article JSON-LD schema and JSX invocation for a blog post.

    Args:
        headline: Article title (max 110 chars recommended for Google)
        date_published: ISO 8601 date string (e.g., '2024-03-15')
        description: Article description / meta description
        author: Author name (default: 'Sourcy Team')
        url: Canonical URL of the article
        image: Featured image URL
        date_modified: Last modified date (defaults to date_published if empty)
    """
    if not headline or not date_published:
        return json.dumps({"error": "headline and date_published are required"})

    json_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline[:110],
        "datePublished": date_published,
        "dateModified": date_modified or date_published,
        "author": [{"@type": "Person", "name": author}],
        "publisher": {
            "@type": "Organization",
            "name": "Sourcy",
            "url": "https://www.sourcy.ai",
            "logo": {"@type": "ImageObject", "url": "https://www.sourcy.ai/logo.png"},
        },
    }
    if description:
        json_ld["description"] = description
    if url:
        json_ld["url"] = url
    if image:
        json_ld["image"] = [image]
    else:
        json_ld["image"] = ["https://www.sourcy.ai/og-image.png"]

    # JSX props
    jsx_props = [f'headline="{headline}"', f'datePublished="{date_published}"']
    if date_modified:
        jsx_props.append(f'dateModified="{date_modified}"')
    if description:
        jsx_props.append(f'description="{description[:200]}"')
    if url:
        jsx_props.append(f'url="{url}"')
    if image:
        jsx_props.append(f'image="{image}"')
    if author != "Sourcy Team":
        jsx_props.append(f'author="{author}"')

    jsx = f'<ArticleLD {" ".join(jsx_props)} />'
    jsx_import = 'import { ArticleLD } from "@/components/seo/StructuredData";'

    script_tag = (
        '<script type="application/ld+json">\n'
        + json.dumps(json_ld, indent=2)
        + '\n</script>'
    )

    return json.dumps({
        "schema_type": "Article",
        "headline": headline,
        "json_ld": json_ld,
        "script_tag": script_tag,
        "jsx_invocation": jsx,
        "jsx_import": jsx_import,
    })


# ─── Breadcrumb Schema ────────────────────────────────────────────────────────

@function_tool
def generate_breadcrumb_schema(
    breadcrumbs_json: str,
) -> str:
    """Generate BreadcrumbList JSON-LD and JSX invocation.

    Args:
        breadcrumbs_json: JSON array of {name, url} objects in order.
                          Example: '[{"name": "Home", "url": "https://sourcy.ai/"},
                                    {"name": "Blogs", "url": "https://sourcy.ai/blogs/"}]'
    """
    try:
        items = json.loads(breadcrumbs_json)
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps({"error": f"Invalid breadcrumbs_json: {str(e)}"})

    if not isinstance(items, list) or len(items) < 2:
        return json.dumps({"error": "breadcrumbs_json must be an array with at least 2 items"})

    json_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": item["name"],
                "item": item["url"],
            }
            for i, item in enumerate(items)
        ],
    }

    items_prop = json.dumps(items, indent=2)
    jsx = f'<BreadcrumbLD items={{{items_prop}}} />'
    jsx_import = 'import { BreadcrumbLD } from "@/components/seo/StructuredData";'

    script_tag = (
        '<script type="application/ld+json">\n'
        + json.dumps(json_ld, indent=2)
        + '\n</script>'
    )

    return json.dumps({
        "schema_type": "BreadcrumbList",
        "item_count": len(items),
        "json_ld": json_ld,
        "script_tag": script_tag,
        "jsx_invocation": jsx,
        "jsx_import": jsx_import,
    })


# ─── Organization Schema ──────────────────────────────────────────────────────

@function_tool
def generate_organization_schema(
    name: str = "Sourcy",
    url: str = "https://www.sourcy.ai",
    description: str = "Sourcy helps brands source from China with vetted suppliers, QA, and fast quotations.",
    logo: str = "https://www.sourcy.ai/logo.png",
    same_as_json: str = "",
) -> str:
    """Generate Organization JSON-LD and JSX invocation.

    Args:
        name: Organization name
        url: Organization website URL
        description: Short description (used for AEO/GEO entity signals)
        logo: Logo image URL
        same_as_json: JSON array of social profile URLs (optional)
    """
    same_as = []
    if same_as_json:
        try:
            same_as = json.loads(same_as_json)
        except (json.JSONDecodeError, TypeError):
            pass

    if not same_as:
        same_as = [
            "https://www.linkedin.com/company/sourcy-global/",
            "https://twitter.com/sourcyapp",
            "https://www.instagram.com/sourcyapp/",
        ]

    json_ld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
        "url": url,
        "logo": logo,
        "description": description,
        "sameAs": same_as,
    }

    # JSX - use defaults (component already has them)
    jsx_parts = []
    if name != "Sourcy":
        jsx_parts.append(f'name="{name}"')
    if description != "Sourcy helps brands source from China with vetted suppliers, QA, and fast quotations.":
        jsx_parts.append(f'description="{description}"')
    jsx_props = " ".join(jsx_parts)
    jsx = f'<OrganizationLD {jsx_props} />' if jsx_props else '<OrganizationLD />'
    jsx_import = 'import { OrganizationLD } from "@/components/seo/StructuredData";'

    script_tag = (
        '<script type="application/ld+json">\n'
        + json.dumps(json_ld, indent=2)
        + '\n</script>'
    )

    return json.dumps({
        "schema_type": "Organization",
        "json_ld": json_ld,
        "script_tag": script_tag,
        "jsx_invocation": jsx,
        "jsx_import": jsx_import,
    })


# ─── Service Schema ───────────────────────────────────────────────────────────

@function_tool
def generate_service_schema(
    name: str,
    description: str,
    url: str = "https://www.sourcy.ai",
    image: str = "",
    area_served: str = "Worldwide",
) -> str:
    """Generate Service JSON-LD and JSX invocation for a Sourcy service page.

    Args:
        name: Service name (e.g., 'China Sourcing Service', 'Product Catalog Creation')
        description: Detailed service description (2-3 sentences)
        url: Service page URL
        image: Service image URL (optional)
        area_served: Geographic area served (default: 'Worldwide')
    """
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "description": description,
        "provider": {
            "@type": "Organization",
            "name": "Sourcy",
            "url": "https://www.sourcy.ai",
            "logo": {"@type": "ImageObject", "url": "https://www.sourcy.ai/logo.png"},
        },
        "url": url,
        "image": image or "https://www.sourcy.ai/og-image.png",
        "areaServed": area_served,
    }

    jsx_props = [f'name="{name}"', f'description="{description[:300]}"', f'url="{url}"']
    if area_served != "Worldwide":
        jsx_props.append(f'areaServed="{area_served}"')
    if image:
        jsx_props.append(f'image="{image}"')

    jsx = f'<ServiceLD {" ".join(jsx_props)} />'
    jsx_import = 'import { ServiceLD } from "@/components/seo/StructuredData";'

    script_tag = (
        '<script type="application/ld+json">\n'
        + json.dumps(json_ld, indent=2)
        + '\n</script>'
    )

    return json.dumps({
        "schema_type": "Service",
        "name": name,
        "json_ld": json_ld,
        "script_tag": script_tag,
        "jsx_invocation": jsx,
        "jsx_import": jsx_import,
    })


# ─── Multi-schema bundler ─────────────────────────────────────────────────────

@function_tool
def generate_page_schema_bundle(
    page_type: str,
    page_metadata_json: str,
) -> str:
    """Generate a complete set of schemas appropriate for a given page type.

    Returns all relevant JSON-LD schemas + JSX invocations in one call.

    Args:
        page_type: Page type — 'blog', 'homepage', 'service', 'about', 'trends', 'sourcing'
        page_metadata_json: JSON object with page metadata. Required keys depend on page_type:
            - blog: {headline, date_published, url, description?, author?, image?, faqs?}
            - homepage: {description?}
            - service: {name, description, url}
            - about: {description?}
            - trends: {name, description, url}
            - sourcing: {name, description, url}
    """
    try:
        meta = json.loads(page_metadata_json)
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps({"error": f"Invalid page_metadata_json: {str(e)}"})

    schemas = []
    jsx_blocks = []
    imports_needed = set()

    pt = page_type.lower()

    if pt == "blog":
        # Article + BreadcrumbList + FAQPage (if faqs provided) + OrganizationLD
        art = json.loads(generate_article_schema.__wrapped__(
            headline=meta.get("headline", ""),
            date_published=meta.get("date_published", ""),
            description=meta.get("description", ""),
            author=meta.get("author", "Sourcy Team"),
            url=meta.get("url", ""),
            image=meta.get("image", ""),
            date_modified=meta.get("date_modified", ""),
        ))
        if "error" not in art:
            schemas.append(art["json_ld"])
            jsx_blocks.append(art["jsx_invocation"])
            imports_needed.add(art["jsx_import"])

        if meta.get("url"):
            bc = json.loads(generate_breadcrumb_schema.__wrapped__(
                breadcrumbs_json=json.dumps([
                    {"name": "Home", "url": "https://www.sourcy.ai/"},
                    {"name": "Blogs", "url": "https://www.sourcy.ai/blogs/"},
                    {"name": meta.get("headline", "Article"), "url": meta["url"]},
                ])
            ))
            if "error" not in bc:
                schemas.append(bc["json_ld"])
                jsx_blocks.append(bc["jsx_invocation"])
                imports_needed.add(bc["jsx_import"])

        if meta.get("faqs"):
            faqs = meta["faqs"]
            faqs_json = json.dumps(faqs) if isinstance(faqs, list) else faqs
            faq = json.loads(generate_faq_schema.__wrapped__(
                faqs_json=faqs_json,
                page_url=meta.get("url", ""),
            ))
            if "error" not in faq:
                schemas.append(faq["json_ld"])
                jsx_blocks.append(faq["jsx_invocation"])
                imports_needed.add(faq["jsx_import"])

    elif pt == "homepage":
        org = json.loads(generate_organization_schema.__wrapped__(
            description=meta.get("description", "Sourcy helps brands source from China with vetted suppliers, QA, and fast quotations."),
        ))
        schemas.append(org["json_ld"])
        jsx_blocks.append(org["jsx_invocation"])
        imports_needed.add(org["jsx_import"])

        ws = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "url": "https://www.sourcy.ai",
            "name": "Sourcy",
            "potentialAction": {
                "@type": "SearchAction",
                "target": "https://www.sourcy.ai/search?q={query}",
                "query-input": "required name=query",
            },
        }
        schemas.append(ws)
        jsx_blocks.append('<WebSiteLD />')
        imports_needed.add('import { WebSiteLD } from "@/components/seo/StructuredData";')

    elif pt in ("service", "sourcing", "trends"):
        svc = json.loads(generate_service_schema.__wrapped__(
            name=meta.get("name", "Sourcy Service"),
            description=meta.get("description", ""),
            url=meta.get("url", "https://www.sourcy.ai"),
        ))
        if "error" not in svc:
            schemas.append(svc["json_ld"])
            jsx_blocks.append(svc["jsx_invocation"])
            imports_needed.add(svc["jsx_import"])

        if meta.get("faqs"):
            faqs_json = json.dumps(meta["faqs"]) if isinstance(meta.get("faqs"), list) else meta.get("faqs", "[]")
            faq = json.loads(generate_faq_schema.__wrapped__(faqs_json=faqs_json))
            if "error" not in faq:
                schemas.append(faq["json_ld"])
                jsx_blocks.append(faq["jsx_invocation"])
                imports_needed.add(faq["jsx_import"])

    # Combined imports line
    all_named = []
    for imp in sorted(imports_needed):
        # Extract named imports from 'import { X } from "..."' pattern
        import_match = __import__("re").search(r'\{([^}]+)\}', imp)
        if import_match:
            all_named.extend([n.strip() for n in import_match.group(1).split(",")])

    combined_import = (
        f'import {{ {", ".join(sorted(set(all_named)))} }} from "@/components/seo/StructuredData";'
        if all_named else ""
    )

    return json.dumps({
        "page_type": page_type,
        "schema_count": len(schemas),
        "schemas": schemas,
        "jsx_invocations": jsx_blocks,
        "jsx_invocations_combined": "\n".join(jsx_blocks),
        "combined_import": combined_import,
        "individual_imports": list(imports_needed),
        "instructions": (
            f"Add '{combined_import}' to page imports, "
            f"then place the JSX invocations inside the page component return."
        ),
    })
