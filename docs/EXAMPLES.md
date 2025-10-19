# AI Browser Agent Usage Examples

## Table of Contents
- [Basic Examples](#basic-examples)
- [Email Management](#email-management)
- [Online Shopping](#online-shopping)
- [Web Navigation](#web-navigation)
- [Form Filling](#form-filling)
- [Information Extraction](#information-extraction)
- [Account Management](#account-management)
- [Advanced Workflows](#advanced-workflows)

---

## Basic Examples

### Simple Navigation
```bash
# Navigate to a website
ai-browser-agent --task "Go to google.com"

# Navigate and perform search
ai-browser-agent --task "Go to google.com and search for 'AI automation'"

# Navigate and extract information
ai-browser-agent --task "Go to example.com and tell me the page title"
```

### Basic Interactions
```bash
# Click elements
ai-browser-agent --task "Go to github.com and click the Sign In button"

# Fill forms
ai-browser-agent --task "Go to google.com, search for 'weather', and tell me today's forecast"

# Wait for content
ai-browser-agent --task "Go to news.ycombinator.com and wait for the page to load, then tell me the top story"
```

---

## Email Management

### Gmail Tasks

#### Basic Email Operations
```bash
# Check inbox summary
ai-browser-agent --task "Go to Gmail and tell me how many unread emails I have"

# Read recent emails
ai-browser-agent --task "Check my Gmail inbox and summarize the 5 most recent emails"

# Delete spam emails
ai-browser-agent --task "Go through my Gmail inbox and delete any obvious spam emails"

# Mark emails as read
ai-browser-agent --task "Mark all unread emails from newsletters as read in Gmail"
```

#### Advanced Email Management
```bash
# Organize by sender
ai-browser-agent --task "In Gmail, move all emails from 'notifications@github.com' to the 'GitHub' label"

# Clean up old emails
ai-browser-agent --task "Delete all emails in Gmail's Promotions tab that are older than 30 days"

# Unsubscribe from lists
ai-browser-agent --task "Find emails with unsubscribe links that I haven't opened in 3 months and unsubscribe from them"

# Create email filters
ai-browser-agent --task "Create a Gmail filter to automatically label emails from 'noreply@company.com' as 'Work Notifications'"
```

#### Email Search and Analysis
```bash
# Search for specific emails
ai-browser-agent --task "Search Gmail for emails from my boss containing 'meeting' and tell me about them"

# Analyze email patterns
ai-browser-agent --task "Look at my Gmail inbox and tell me which senders email me most frequently"

# Find important emails
ai-browser-agent --task "Find any emails in Gmail marked as important that I haven't read yet"
```

### Other Email Providers

#### Outlook/Hotmail
```bash
# Basic Outlook tasks
ai-browser-agent --task "Go to Outlook.com, check my inbox, and delete any spam"

# Organize Outlook emails
ai-browser-agent --task "In Outlook, move all emails from social media notifications to the 'Social' folder"
```

#### Yahoo Mail
```bash
# Yahoo Mail management
ai-browser-agent --task "Check my Yahoo Mail inbox and tell me about any urgent emails"

# Clean Yahoo Mail
ai-browser-agent --task "Delete all emails in Yahoo Mail's spam folder"
```

---

## Online Shopping

### Amazon Shopping

#### Product Search
```bash
# Basic product search
ai-browser-agent --task "Go to Amazon and search for wireless headphones under $100"

# Specific product search
ai-browser-agent --task "Find the Apple AirPods Pro on Amazon and tell me the current price"

# Compare products
ai-browser-agent --task "Search Amazon for 'laptop bags' and compare the top 3 results by price and rating"
```

#### Shopping Cart Management
```bash
# Add items to cart
ai-browser-agent --task "Add a pack of AA batteries to my Amazon cart"

# Review cart
ai-browser-agent --task "Go to my Amazon cart and tell me what's in it and the total price"

# Remove items from cart
ai-browser-agent --task "Remove any items from my Amazon cart that cost more than $50"
```

#### Order Management
```bash
# Check order status
ai-browser-agent --task "Check the status of my most recent Amazon order"

# View order history
ai-browser-agent --task "Go to my Amazon order history and tell me what I ordered last month"

# Track packages
ai-browser-agent --task "Find any Amazon packages that are out for delivery today"
```

### Food Delivery

#### DoorDash
```bash
# Browse restaurants
ai-browser-agent --task "Go to DoorDash and show me pizza places that deliver to my area"

# Repeat previous order
ai-browser-agent --task "Go to DoorDash and reorder my last pizza order"

# Find specific cuisine
ai-browser-agent --task "Find Thai restaurants on DoorDash with ratings above 4.5 stars"
```

#### Uber Eats
```bash
# Search for food
ai-browser-agent --task "Search Uber Eats for 'sushi' and find the highest-rated restaurant"

# Check delivery time
ai-browser-agent --task "Go to Uber Eats and tell me the estimated delivery time for McDonald's"
```

#### Grubhub
```bash
# Browse by category
ai-browser-agent --task "Go to Grubhub and find Italian restaurants that are currently open"

# Check promotions
ai-browser-agent --task "Look for any current promotions or deals on Grubhub"
```

### Other E-commerce Sites

#### eBay
```bash
# Search auctions
ai-browser-agent --task "Search eBay for 'vintage camera' and find auctions ending today"

# Check selling prices
ai-browser-agent --task "Look up recently sold iPhone 13 Pro on eBay and tell me the average price"
```

#### Etsy
```bash
# Find handmade items
ai-browser-agent --task "Search Etsy for handmade leather wallets and show me the top 3 results"
```

---

## Web Navigation

### News and Information

#### News Websites
```bash
# Get latest news
ai-browser-agent --task "Go to BBC News and tell me the top 3 headlines"

# Find specific news
ai-browser-agent --task "Search CNN for news about artificial intelligence from this week"

# Compare news sources
ai-browser-agent --task "Check both Reuters and AP News for stories about the latest tech earnings"
```

#### Wikipedia Research
```bash
# Basic Wikipedia lookup
ai-browser-agent --task "Go to Wikipedia and look up information about machine learning"

# Follow Wikipedia links
ai-browser-agent --task "Start at the Wikipedia page for 'Python programming' and follow links to find information about its creator"
```

### Social Media

#### Twitter/X
```bash
# Check trending topics
ai-browser-agent --task "Go to Twitter and tell me what's trending today"

# Search tweets
ai-browser-agent --task "Search Twitter for tweets about 'AI automation' from the past 24 hours"
```

#### LinkedIn
```bash
# Check notifications
ai-browser-agent --task "Go to LinkedIn and check if I have any new connection requests"

# Browse jobs
ai-browser-agent --task "Search LinkedIn Jobs for 'software engineer' positions in San Francisco"
```

### Entertainment

#### YouTube
```bash
# Search videos
ai-browser-agent --task "Go to YouTube and find tutorials about Python programming"

# Check subscriptions
ai-browser-agent --task "Go to my YouTube subscriptions and tell me if any of my favorite channels posted new videos"
```

#### Netflix
```bash
# Browse content
ai-browser-agent --task "Go to Netflix and find new sci-fi movies added this month"

# Check watchlist
ai-browser-agent --task "Look at my Netflix watchlist and recommend something to watch tonight"
```

---

## Form Filling

### Contact Forms
```bash
# Basic contact form
ai-browser-agent --task "Go to example.com/contact and fill out the form with: Name: John Doe, Email: john@example.com, Message: I'm interested in your services"

# Support ticket
ai-browser-agent --task "Fill out the support form on company.com with my account issue: Account: john123, Issue: Cannot reset password"
```

### Registration Forms
```bash
# Newsletter signup
ai-browser-agent --task "Sign up for the newsletter on techblog.com using email: john@example.com"

# Event registration
ai-browser-agent --task "Register for the webinar on marketing.com using: Name: John Doe, Company: TechCorp, Email: john@techcorp.com"
```

### Survey Forms
```bash
# Customer feedback
ai-browser-agent --task "Fill out the customer satisfaction survey on retailer.com rating everything as 'Excellent'"

# Product review
ai-browser-agent --task "Leave a 5-star review for the wireless headphones on the product page, mentioning good sound quality"
```

---

## Information Extraction

### Price Monitoring
```bash
# Check product prices
ai-browser-agent --task "Check the price of iPhone 15 Pro on Apple's website and Best Buy, then compare them"

# Monitor stock availability
ai-browser-agent --task "Check if the PlayStation 5 is in stock on Target, Walmart, and GameStop"
```

### Real Estate
```bash
# Property search
ai-browser-agent --task "Go to Zillow and find 3-bedroom houses for sale in Austin, Texas under $400k"

# Market analysis
ai-browser-agent --task "Look up recent home sales in zip code 78701 on Realtor.com and tell me the average price"
```

### Job Market
```bash
# Job search
ai-browser-agent --task "Search Indeed for 'data scientist' jobs in New York and tell me the salary ranges"

# Company research
ai-browser-agent --task "Go to Glassdoor and find employee reviews for Google's software engineering positions"
```

### Financial Information
```bash
# Stock prices
ai-browser-agent --task "Check the current stock price of Apple (AAPL) on Yahoo Finance"

# Market news
ai-browser-agent --task "Go to MarketWatch and find the latest news about cryptocurrency markets"
```

---

## Account Management

### Profile Updates

#### Social Media Profiles
```bash
# LinkedIn profile
ai-browser-agent --task "Go to my LinkedIn profile and update my headline to 'Senior Software Engineer at TechCorp'"

# Twitter bio
ai-browser-agent --task "Update my Twitter bio to include 'AI enthusiast and developer'"
```

#### Professional Profiles
```bash
# GitHub profile
ai-browser-agent --task "Go to my GitHub profile and update my bio to mention my expertise in Python and machine learning"

# Portfolio website
ai-browser-agent --task "Update the 'About' section on my portfolio website with my latest job title and skills"
```

### Settings Management

#### Privacy Settings
```bash
# Facebook privacy
ai-browser-agent --task "Go to Facebook privacy settings and make sure my posts are only visible to friends"

# Google account
ai-browser-agent --task "Check my Google account privacy settings and turn off ad personalization"
```

#### Notification Settings
```bash
# Email notifications
ai-browser-agent --task "Go to my LinkedIn settings and turn off email notifications for connection requests"

# App notifications
ai-browser-agent --task "Update my Twitter notification settings to only notify me for direct messages"
```

### Subscription Management
```bash
# Cancel subscriptions
ai-browser-agent --task "Go to my Netflix account settings and cancel my subscription"

# Upgrade plans
ai-browser-agent --task "Upgrade my Spotify account from free to premium"

# Check billing
ai-browser-agent --task "Go to my Amazon Prime account and check when my next billing date is"
```

---

## Advanced Workflows

### Multi-Step Tasks

#### Research Workflow
```bash
ai-browser-agent --task "Research the latest iPhone model: First, go to Apple's website and get the specs and price. Then, check reviews on CNET and TechCrunch. Finally, compare prices on Amazon and Best Buy."
```

#### Shopping Comparison
```bash
ai-browser-agent --task "I want to buy a laptop: Search for 'MacBook Air M2' on Amazon, Best Buy, and Apple's website. Compare prices, availability, and shipping options. Then tell me which offers the best deal."
```

#### Email and Calendar Management
```bash
ai-browser-agent --task "Check my Gmail for any meeting invitations from this week. For each invitation, go to Google Calendar and make sure the meeting is added. If any are missing, add them manually."
```

### Automated Monitoring

#### Price Tracking
```bash
ai-browser-agent --task "Check the price of the item in my Amazon wishlist. If any item has dropped in price by more than 10%, add it to my cart."
```

#### News Monitoring
```bash
ai-browser-agent --task "Check TechCrunch, The Verge, and Ars Technica for any news about OpenAI or Anthropic from today. Summarize any important developments."
```

#### Social Media Monitoring
```bash
ai-browser-agent --task "Check my company's Twitter mentions and LinkedIn page for any customer feedback or questions that need responses."
```

### Data Collection

#### Market Research
```bash
ai-browser-agent --task "Visit the websites of our top 5 competitors and collect information about their pricing, features, and latest product announcements."
```

#### Lead Generation
```bash
ai-browser-agent --task "Search LinkedIn for 'marketing directors' at companies in the tech industry with 100-500 employees. Collect their names and company information."
```

#### Content Curation
```bash
ai-browser-agent --task "Find the top 10 most popular articles about AI automation from this week across Medium, Harvard Business Review, and MIT Technology Review."
```

### Workflow Automation

#### Daily Routine
```bash
ai-browser-agent --task "My morning routine: Check Gmail for urgent emails, look at today's weather forecast, check my calendar for meetings, and browse the top tech news headlines."
```

#### Weekly Tasks
```bash
ai-browser-agent --task "Weekly review: Check my Amazon orders from this week, review my Netflix watch history, and see if there are any new episodes of my favorite shows."
```

#### Monthly Maintenance
```bash
ai-browser-agent --task "Monthly cleanup: Go through my Gmail and delete emails older than 6 months from the Promotions folder. Then check my subscription services and see if I'm still using them all."
```

---

## Tips for Effective Task Descriptions

### Be Specific
```bash
# Good: Specific and clear
ai-browser-agent --task "Go to Amazon, search for 'wireless mouse', filter by 4+ star ratings, and show me the top 3 results under $30"

# Avoid: Too vague
ai-browser-agent --task "Find me a good mouse"
```

### Break Down Complex Tasks
```bash
# Good: Step-by-step approach
ai-browser-agent --task "First, go to my Gmail inbox"
ai-browser-agent --task "Now, look for emails from 'newsletter@company.com' and move them to the 'Newsletters' folder"

# Avoid: Too many steps at once
ai-browser-agent --task "Manage my entire email inbox, organize everything, delete spam, unsubscribe from lists, and create filters"
```

### Provide Context
```bash
# Good: Includes necessary context
ai-browser-agent --task "Go to my Amazon account (I'm already logged in) and check the status of order #123-456789"

# Good: Specifies expected behavior
ai-browser-agent --task "Search Google for 'best pizza near me' and tell me the top 3 restaurants with their ratings"
```

### Handle Security Appropriately
```bash
# Good: Acknowledges security needs
ai-browser-agent --task "Go to my bank's website and check my account balance. I'll confirm any security prompts that appear."

# Good: Stops before sensitive actions
ai-browser-agent --task "Add items to my Amazon cart but don't proceed to checkout - I'll complete the purchase manually"
```

---

## Error Handling Examples

### Graceful Degradation
```bash
# The agent will try alternative approaches if the first method fails
ai-browser-agent --task "Find the contact information on company.com. If there's no contact page, look for an 'About' or 'Support' section."
```

### Retry Logic
```bash
# The agent automatically retries failed actions
ai-browser-agent --task "Go to news.ycombinator.com and get the top story. If the page doesn't load, wait 10 seconds and try again."
```

### User Escalation
```bash
# The agent will ask for help when needed
ai-browser-agent --task "Try to log into my email account. If you encounter a CAPTCHA or two-factor authentication, let me know so I can handle it."
```

Remember: The AI Browser Agent is designed to handle complex, multi-step tasks autonomously while maintaining safety through security confirmations and intelligent error handling. Start with simple tasks and gradually increase complexity as you become familiar with the system's capabilities.