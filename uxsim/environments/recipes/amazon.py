# Amazon Web Parsing Recipes
# Based on UXAgent's amazon_recipes.py with adaptations for uxsim

nav = {
    "selector": "#nav-search-bar-form",
    "children": [
        {
            "selector": "input#twotabsearchtextbox",
            "name": "search_input",
        },
        {
            "selector": "#nav-search-submit-button",
            "clickable": True,
            "name": "search_button",
        },
    ],
}

refinement_option = [
    {
        "selector": "span.a-size-base.a-color-base.puis-bold-weight-text",
        "add_text": True,
        "class": "refinement-title",
    },
    {
        "selector": "ul:nth-of-type(1) > span.a-declarative > span > li",
        "add_text": True,
        "name": "from_text",
        "clickable": True,
        "click_selector": "a",
        "direct_child": True,
        "children": [{"selector": "input[type='checkbox']"}],
    },
]

AMAZON_RECIPES = [
    {
        "match": "/",
        "match_method": "url", 
        "selector": "html",
        "children": [
            {"selector": "head", "children": [{"selector": "title", "add_text": True}]},
            {
                "selector": "body",
                "children": [
                    {
                        "selector": "#nav-search-bar-form",
                        "children": [
                            {
                                "selector": "input#twotabsearchtextbox",
                                "name": "search_input",
                            },
                            {
                                "selector": "#nav-search-submit-button",
                                "clickable": True,
                                "name": "search_button",
                            },
                        ],
                    },
                ],
            },
        ],
    },
    {
        "match": "/s",
        "match_method": "url",
        "selector": "html", 
        "children": [
            {"selector": "head", "children": [{"selector": "title", "add_text": True}]},
            {
                "selector": "body",
                "children": [
                    {
                        "selector": "#nav-search-bar-form",
                        "children": [
                            {
                                "selector": "input#twotabsearchtextbox", 
                                "name": "search_input",
                            },
                            {
                                "selector": "#nav-search-submit-button",
                                "clickable": True,
                                "name": "search_button",
                            },
                        ],
                    },
                    {
                        "selector": "#s-refinements",
                        "name": "refinements",
                        "children": [
                            {
                                "selector": "div.a-section.a-spacing-none:not(:has(#n-title)):has(span.a-size-base.a-color-base.puis-bold-weight-text):has(ul span.a-declarative > span > li):not(#reviewsRefinements):not(#departments):not(#priceRefinements):not(#filters)",
                                "name": "from_text",
                                "text_selector": "span.a-size-base.a-color-base.puis-bold-weight-text",
                                "children": [
                                    {
                                        "selector": "span.a-size-base.a-color-base.puis-bold-weight-text",
                                        "add_text": True,
                                        "class": "refinement-title",
                                    },
                                    {
                                        "selector": "ul:nth-of-type(1) > span.a-declarative > span > li",
                                        "add_text": True,
                                        "name": "from_text",
                                        "clickable": True,
                                        "click_selector": "a",
                                        "direct_child": True,
                                        "children": [{"selector": "input[type='checkbox']"}],
                                    },
                                ],
                            },
                            {
                                "selector": "#departments",
                                "name": "departments", 
                                "children": [
                                    {
                                        "selector": "li a",
                                        "add_text": True,
                                        "name": "from_text",
                                        "clickable": True,
                                    }
                                ],
                            },
                            {
                                "selector": "#reviewsRefinements",
                                "name": "reviews_refinements",
                                "children": [
                                    {
                                        "selector": "li a", 
                                        "add_text": True,
                                        "name": "from_text",
                                        "clickable": True,
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "selector": "div.s-main-slot.s-result-list.s-search-results",
                        "name": "search_results",
                        "children": [
                            {
                                "insert_split_marker": True,
                                "insert_split_marker_every": 4,
                                "selector": 'div[data-component-type="s-search-result"]',
                                "text_selector": "span.a-color-base.a-text-normal, h2.a-color-base.a-text-normal span",
                                "name": "from_text",
                                "class": "search-result",
                                "children": [
                                    {
                                        "selector": "div[data-cy='title-recipe'] a.a-link-normal.s-link-style.a-text-normal",
                                        "add_text": True,
                                        "class": "product-name", 
                                        "clickable": True,
                                        "name": "view_product",
                                    },
                                    {
                                        "selector": "div[data-cy='reviews-block']",
                                        "class": "product-review",
                                        "children": [
                                            {
                                                "selector": "span.a-icon-alt",
                                                "add_text": True,
                                                "class": "product-rating",
                                            },
                                            {
                                                "selector": "span.a-size-base.s-underline-text",
                                                "add_text": True,
                                                "text_format": "{} reviews",
                                                "class": "product-rating-count",
                                            },
                                        ],
                                    },
                                    {
                                        "selector": "div[data-cy='price-recipe']",
                                        "class": "product-price",
                                        "children": [
                                            {
                                                "selector": "a.a-link-normal > span.a-price > span.a-offscreen",
                                                "add_text": True,
                                            },
                                        ],
                                    },
                                    {
                                        "selector": "div[data-cy='delivery-recipe']",
                                        "add_text": True,
                                        "class": "product-delivery",
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "selector": "span.s-pagination-strip",
                        "name": "pagination",
                        "children": [
                            {
                                "selector": ".s-pagination-item",
                                "add_text": True,
                                "name": "from_text",
                                "clickable": True,
                            }
                        ],
                    },
                ],
            },
        ],
    },
    {
        "match": "#productTitle",
        "match_text": "",
        "selector": "html",
        "terminate": "return !!arguments[0]",
        "terminate_callback": "return arguments[0]",
        "children": [
            {"selector": "head", "children": [{"selector": "title", "add_text": True}]},
            {
                "selector": "body",
                "children": [
                    {
                        "selector": "#nav-search-bar-form", 
                        "children": [
                            {
                                "selector": "input#twotabsearchtextbox",
                                "name": "search_input",
                            },
                            {
                                "selector": "#nav-search-submit-button",
                                "clickable": True,
                                "name": "search_button",
                            },
                        ],
                    },
                    {
                        "selector": "#productTitle",
                        "add_text": True,
                        "class": "product-title",
                    },
                    {
                        "selector": "#averageCustomerReviews",
                        "class": "customer-reviews",
                        "children": [
                            {
                                "selector": "span.a-icon-alt",
                                "add_text": True,
                                "class": "product-rating",
                            },
                            {
                                "selector": "span.a-size-base.a-color-base", 
                                "add_text": True,
                                "class": "rating-count",
                            },
                        ],
                    },
                    {
                        "selector": "div.a-price-whole",
                        "add_text": True,
                        "class": "price-whole",
                    },
                    {
                        "selector": "div.a-price-fraction",
                        "add_text": True,
                        "class": "price-fraction",
                    },
                    {
                        "selector": "#add-to-cart-button",
                        "clickable": True,
                        "name": "add_to_cart",
                        "add_text": True,
                    },
                    {
                        "selector": "#buy-now-button",
                        "clickable": True,
                        "name": "buy_now",
                        "add_text": True,
                    },
                    {
                        "selector": "#feature-bullets ul",
                        "children": [
                            {
                                "selector": "li",
                                "add_text": True,
                                "class": "product-feature",
                            }
                        ],
                    },
                    {
                        "selector": "#productDescription",
                        "add_text": True,
                        "class": "product-description",
                    },
                ],
            },
        ],
    },
    {
        "match": "/gp/cart",
        "match_method": "url",
        "selector": "html",
        "children": [
            {"selector": "head", "children": [{"selector": "title", "add_text": True}]},
            {
                "selector": "body",
                "children": [
                    {
                        "selector": "#nav-search-bar-form",
                        "children": [
                            {
                                "selector": "input#twotabsearchtextbox",
                                "name": "search_input",
                            },
                            {
                                "selector": "#nav-search-submit-button",
                                "clickable": True,
                                "name": "search_button",
                            },
                        ],
                    },
                    {
                        "selector": "#sc-active-cart",
                        "name": "cart_items",
                        "children": [
                            {
                                "selector": "div[data-name='Active Items']",
                                "name": "cart_item",
                                "children": [
                                    {
                                        "selector": "span[data-component-type='s-product-image'] img",
                                        "name": "product_image",
                                    },
                                    {
                                        "selector": "h4.a-size-base-plus a",
                                        "add_text": True,
                                        "clickable": True,
                                        "name": "product_link",
                                    },
                                    {
                                        "selector": "span.a-price.a-text-price.a-size-medium.a-color-base",
                                        "add_text": True,
                                        "class": "item-price",
                                    },
                                    {
                                        "selector": "input[name='quantity']",
                                        "name": "quantity_input",
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "selector": "#sc-subtotal-amount-activecart",
                        "add_text": True,
                        "class": "cart-subtotal",
                    },
                    {
                        "selector": "input[name='proceedToRetailCheckout']",
                        "clickable": True,
                        "name": "proceed_to_checkout",
                        "add_text": True,
                    },
                ],
            },
        ],
    },
]

# Additional utility functions for Amazon-specific behavior
def get_amazon_config():
    """Get configuration for Amazon environment"""
    return {
        "start_url": "https://www.amazon.com",
        "recipes": AMAZON_RECIPES,
        "wait_time": 2,
        "max_retries": 3,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def extract_amazon_product_info(page_data):
    """Extract structured product information from Amazon page"""
    info = {}
    
    # Extract basic product info
    if "product-title" in page_data:
        info["title"] = page_data["product-title"]
    
    if "product-rating" in page_data:
        info["rating"] = page_data["product-rating"]
        
    if "rating-count" in page_data:
        info["review_count"] = page_data["rating-count"]
        
    # Extract price
    price_parts = []
    if "price-whole" in page_data:
        price_parts.append(page_data["price-whole"])
    if "price-fraction" in page_data:
        price_parts.append(page_data["price-fraction"])
    
    if price_parts:
        info["price"] = ".".join(price_parts)
    
    # Extract features
    if "product-feature" in page_data:
        info["features"] = page_data["product-feature"]
        
    if "product-description" in page_data:
        info["description"] = page_data["product-description"] 
        
    return info 