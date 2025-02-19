- **Core:** Global settings, middleware, and (basic) user account management.
- **Data_Engine:** Handles data aggregation, parsing, and AI processing (including the chat interface).
- **Notifier:** Manages notification delivery, user preferences.

---

## **Feature 1: Multi‑Source Data Aggregation and Parsing**

**Objective:**  
Automatically collect and extract key notification information from various external sources (websites and PDFs).

**What We Are Doing:**  
- **Web Scraping:** Regularly crawl designated websites to fetch HTML-based notifications.  
- **PDF Parsing:** Download and parse PDF documents to extract textual content (e.g., exam schedules, registration details).  
- **Preliminary Data Extraction:** Identify and extract raw elements like dates, titles, and document links for further processing.

**How We Are Doing It:**  
- **Implementation:**  
  - **Scraping:** Use libraries such as *BeautifulSoup* (or *Scrapy*) to navigate and extract HTML data.  
  - **PDF Parsing:** Utilize libraries like *pdfminer.six* or *PyPDF2* to extract text from PDFs.  
  - **Task Scheduling:** Employ Celery (or Django Q) to run periodic scraping/parsing tasks.  
  - **Error Handling & Logging:** Implement robust logging and error detection for failed tasks.

**Integration:**  
- This feature feeds its raw output into the next stage (AI-based chat/data processing) within the **Data_Engine** app.

**Data Storage (Models in `data_engine/models.py`):**  
- **WebsiteConfig**  
  - *Fields:* `id`, `url`, `scraping_frequency`, `last_scrape_date`, `auth_info` (if needed).  
- **ScrapeTaskLog**  
  - *Fields:* `id`, `website` (FK to WebsiteConfig), `status` (e.g., success/failure), `timestamp`, `error_message` (optional).  
- **RawNotification**  
  - *Fields:* `id`, `website` (FK), `content` (raw text or HTML), `document_type` (choices: 'html', 'pdf'), `scraped_date`.

**Possible Alternatives:**  
- Use a cloud-based scraping service if scaling becomes an issue.  
- Consider Scrapy for a more robust scraping framework if BeautifulSoup’s simplicity becomes a bottleneck.

---

## **Feature 2: AI‑Based Chat Interface**

*(This feature merges what was formerly separate “AI Processing” and “Natural Language Query” features.)*

**Objective:**  
Provide an interactive, natural language interface where users can ask questions (e.g., “What is the last date for exam registration?”) and receive human-friendly, context-aware responses.

**What We Are Doing:**  
- **Query Interpretation:** Use NLP to understand user queries, extract intents and key entities (like exam names or dates).  
- **Response Generation:** Map the query to the structured data (derived from parsed notifications) and produce a natural-language response.  
- **Session Management:** Maintain chat sessions to support context and follow-up questions.

**How We Are Doing It:**  
- **Implementation:**  
  - Develop or integrate an AI/chatbot engine using frameworks like *Rasa*, *Dialogflow*, or a custom solution with transformer models (e.g., using HuggingFace).  
  - Expose REST APIs (or GraphQL endpoints) to accept chat queries and return answers based on processed data.  
  - Use context management to support multi-turn dialogues.

**Integration:**  
- The chat interface in the **Data_Engine** app leverages enriched data (from Feature 1) and any additional AI processing to generate responses.
- It also interacts with user preferences (see Feature 4) to tailor responses if needed.

**Data Storage (Models in `data_engine/models.py`):**  
- **ChatSession**  
  - *Fields:* `id`, `user` (FK to Core’s User model, if applicable), `start_time`, `last_interaction`.  
- **ChatMessage**  
  - *Fields:* `id`, `session` (FK to ChatSession), `sender` (choices: 'user' or 'system'), `message_text`, `timestamp`.

**Possible Alternatives:**  
- Outsource the chat functionality to a third-party service if in-house development proves too resource‑intensive.
- Use pre‑trained conversational AI models and fine‑tune them on your domain data.

---

## **Feature 3: Personalized Notification and Alert System**

**Objective:**  
Automatically send targeted notifications and alerts to users regarding important updates (e.g., exam registration deadlines), ensuring timely delivery across multiple channels.

**What We Are Doing:**  
- **Alert Generation:** Monitor processed data for events that match certain criteria (e.g., approaching deadlines) and trigger notifications.  
- **Multi‑Channel Delivery:** Dispatch notifications via email, SMS, or in‑app messages, depending on user preferences.  
- **Status Tracking:** Log notification deliveries and failures for auditing and performance monitoring.

**How We Are Doing It:**  
- **Implementation:**  
  - Use Celery to schedule and run notification tasks.  
  - Integrate with email services (SMTP/SendGrid) and SMS APIs (like Twilio) for delivery.  
  - Develop rules that match processed data with user-defined triggers.

**Integration:**  
- Resides in the **Notifier** app, pulling data from **Data_Engine** (Feature 1/2) and filtering based on user preferences (Feature 4).

**Data Storage (Models in `notifier/models.py`):**  
- **Notification**  
  - *Fields:* `id`, `user` (FK to Core’s User model), `content`, `send_time`, `delivery_channel` (choices: 'email', 'sms', 'in-app'), `status` (e.g., 'pending', 'sent', 'failed').  
- **NotificationHistory** (optional)  
  - *Fields:* `id`, `notification` (FK), `delivery_time`, `result` (e.g., success, error message).

**Possible Alternatives:**  
- Utilize third‑party push notification services to offload delivery complexity.
- Implement in‑app notifications with a real‑time framework like Django Channels if instant delivery is required.

---

## **Feature 4: User Personalization & Preference Management**

**Objective:**  
Empower users to define their interests and preferences so that the content and notifications they receive are tailored to their needs.

**What We Are Doing:**  
- **Preference Setting:** Allow users to specify topics, exam types, or content categories they care about, along with preferred notification channels and frequency.  
- **Content Curation:** Use these preferences to filter and prioritize notifications and chat responses, ensuring relevancy.  
- **Subscription Mapping:** Optionally track “subscriptions” to particular notification categories.

**How We Are Doing It:**  
- **Implementation:**  
  - Develop a user-friendly dashboard (via Django views/forms) for managing preferences.
  - Store settings in the database and integrate them with the notification rules.
  - Optionally, implement a recommendation engine (even simple rule‑based or AI‑assisted) to adjust preferences based on engagement feedback.

**Integration:**  
- Primarily implemented in the **Notifier** app (and partly in **Core** for user management).  
- Feeds into both the Notification System (Feature 3) and AI Chat (Feature 2) to ensure responses and alerts are user‑centric.

**Data Storage (Models in `notifier/models.py`):**  
- **UserPreference**  
  - *Fields:* `id`, `user` (FK to Core’s User model), `preferred_topics` (e.g., JSON or many‑to‑many relation to a Topic model), `notification_channel`, `frequency` (e.g., immediate, daily, weekly).  
- **UserSubscription** (if distinct from preferences)  
  - *Fields:* `id`, `user` (FK), `category` (e.g., exam type), `is_active` (Boolean).

**Possible Alternatives:**  
- Use third‑party personalization/recommendation engines if scaling requires more complex analytics.
- Allow users to import/export their preferences via APIs for cross‑platform synchronization.

---

## **Summary & App Mapping**

- **Core App:**  
  - Handles global settings and basic user management (accounts are referenced in models like `UserPreference`, `ChatSession`, and `Notification` via FK to the user model).

- **Data_Engine App:**  
  - **Feature 1:** Multi-source Data Aggregation and Parsing  
  - **Feature 2:** AI‑Based Chat Interface  
  - Models: `WebsiteConfig`, `ScrapeTaskLog`, `RawNotification`, `ChatSession`, `ChatMessage`.

- **Notifier App:**  
  - **Feature 3:** Personalized Notification and Alert System  
  - **Feature 4:** User Personalization & Preference Management 
  - Models: `Notification`, `NotificationHistory`, `UserPreference`, `UserSubscription`, `UserEngagement`, `SystemLog`.
