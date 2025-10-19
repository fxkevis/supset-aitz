"""Email management task handler for automated email operations."""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ai_browser_agent.interfaces.base_interfaces import BaseTaskHandler
from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.controllers.element_locator import ElementLocator
from ai_browser_agent.controllers.page_analyzer import PageAnalyzer
from ai_browser_agent.managers.context_manager import ContextManager
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.page_content import PageContent


logger = logging.getLogger(__name__)


@dataclass
class EmailMetadata:
    """Metadata for an email message."""
    subject: str
    sender: str
    sender_email: str
    date: datetime
    is_read: bool
    is_spam: bool
    folder: str
    element_selector: str  # Selector to interact with this email
    content_preview: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "subject": self.subject,
            "sender": self.sender,
            "sender_email": self.sender_email,
            "date": self.date.isoformat(),
            "is_read": self.is_read,
            "is_spam": self.is_spam,
            "folder": self.folder,
            "element_selector": self.element_selector,
            "content_preview": self.content_preview
        }


@dataclass
class SpamAnalysisResult:
    """Result of spam analysis for an email."""
    is_spam: bool
    confidence: float
    reasons: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_spam": self.is_spam,
            "confidence": self.confidence,
            "reasons": self.reasons
        }


class EmailServiceDetector:
    """Detects and handles different email service providers."""
    
    SUPPORTED_SERVICES = {
        "gmail": {
            "domains": ["mail.google.com", "gmail.com"],
            "inbox_selectors": [
                "[data-tooltip='Inbox']",
                "a[href*='#inbox']",
                ".aim[title*='Inbox']"
            ],
            "email_list_selectors": [
                "tr.zA",  # Gmail conversation rows
                ".Cp .aDP",  # Gmail email rows
                "[role='main'] tr"
            ],
            "email_subject_selectors": [
                ".bog",  # Gmail subject
                "span[id*=':']",  # Gmail subject span
                ".y6 span"
            ],
            "sender_selectors": [
                ".yW span",  # Gmail sender
                ".go span[email]",
                ".yX span"
            ],
            "delete_selectors": [
                "[data-tooltip='Delete']",
                ".ar9 .T-I[act='10']"
            ],
            "spam_selectors": [
                "[data-tooltip='Report spam']",
                ".ar9 .T-I[act='102']"
            ]
        },
        "outlook": {
            "domains": ["outlook.live.com", "outlook.office.com", "hotmail.com"],
            "inbox_selectors": [
                "[aria-label='Inbox']",
                "button[title*='Inbox']",
                ".o365cs-nav-leftNav [title*='Inbox']"
            ],
            "email_list_selectors": [
                "[role='listitem'][aria-label*='message']",
                ".customScrollBar [role='option']",
                "div[data-convid]"
            ],
            "email_subject_selectors": [
                "[data-testid='message-subject']",
                ".JNdkSc",
                "span[title]"
            ],
            "sender_selectors": [
                "[data-testid='message-sender']",
                ".zItAjt",
                ".JNdkSc + div"
            ],
            "delete_selectors": [
                "[aria-label='Delete']",
                "button[title*='Delete']"
            ],
            "spam_selectors": [
                "[aria-label*='Junk']",
                "button[title*='Junk']"
            ]
        },
        "yahoo": {
            "domains": ["mail.yahoo.com"],
            "inbox_selectors": [
                "[data-test-id='folder-inbox']",
                "a[href*='folder=Inbox']"
            ],
            "email_list_selectors": [
                "[data-test-id='message-list-item']",
                ".message-list-item",
                "li[data-test-id*='message']"
            ],
            "email_subject_selectors": [
                "[data-test-id='message-subject']",
                ".subject",
                "span[title]"
            ],
            "sender_selectors": [
                "[data-test-id='message-from']",
                ".from",
                ".sender"
            ],
            "delete_selectors": [
                "[data-test-id='delete-button']",
                "button[title*='Delete']"
            ],
            "spam_selectors": [
                "[data-test-id='spam-button']",
                "button[title*='Spam']"
            ]
        }
    }
    
    @classmethod
    def detect_service(cls, url: str) -> Optional[str]:
        """Detect email service from URL."""
        for service, config in cls.SUPPORTED_SERVICES.items():
            for domain in config["domains"]:
                if domain in url.lower():
                    return service
        return None
    
    @classmethod
    def get_service_config(cls, service: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific email service."""
        return cls.SUPPORTED_SERVICES.get(service)


class SpamDetector:
    """Analyzes emails to detect spam based on various criteria."""
    
    # Common spam indicators
    SPAM_KEYWORDS = [
        "urgent", "act now", "limited time", "free money", "guaranteed",
        "no obligation", "risk free", "winner", "congratulations",
        "click here", "buy now", "order now", "subscribe", "unsubscribe",
        "viagra", "casino", "lottery", "inheritance", "prince",
        "million dollars", "tax refund", "irs", "paypal suspended"
    ]
    
    SUSPICIOUS_DOMAINS = [
        "tempmail", "10minutemail", "guerrillamail", "mailinator",
        "throwaway", "temp-mail", "fakeinbox"
    ]
    
    SPAM_PATTERNS = [
        r'\$\d+',  # Money amounts
        r'[A-Z]{3,}',  # Excessive caps
        r'!!!+',  # Multiple exclamation marks
        r'\d+%\s*(off|discount)',  # Percentage discounts
        r'(free|win|won)\s*(money|cash|\$)',  # Free money offers
    ]
    
    def analyze_email(self, email_metadata: EmailMetadata) -> SpamAnalysisResult:
        """Analyze an email for spam indicators."""
        reasons = []
        spam_score = 0.0
        
        # Check subject for spam keywords
        subject_lower = email_metadata.subject.lower()
        keyword_matches = sum(1 for keyword in self.SPAM_KEYWORDS if keyword in subject_lower)
        if keyword_matches > 0:
            spam_score += keyword_matches * 0.2
            reasons.append(f"Contains {keyword_matches} spam keywords in subject")
        
        # Check for suspicious sender domain
        sender_domain = email_metadata.sender_email.split('@')[-1].lower()
        if any(suspicious in sender_domain for suspicious in self.SUSPICIOUS_DOMAINS):
            spam_score += 0.4
            reasons.append("Sender uses suspicious domain")
        
        # Check for spam patterns in subject
        pattern_matches = sum(1 for pattern in self.SPAM_PATTERNS 
                            if re.search(pattern, email_metadata.subject, re.IGNORECASE))
        if pattern_matches > 0:
            spam_score += pattern_matches * 0.15
            reasons.append(f"Contains {pattern_matches} spam patterns")
        
        # Check sender reputation (simplified)
        if self._is_suspicious_sender(email_metadata.sender_email):
            spam_score += 0.3
            reasons.append("Suspicious sender address format")
        
        # Check content preview if available
        if email_metadata.content_preview:
            content_score = self._analyze_content(email_metadata.content_preview)
            spam_score += content_score
            if content_score > 0.2:
                reasons.append("Suspicious content patterns")
        
        # Determine if spam (threshold: 0.5)
        is_spam = spam_score >= 0.5
        confidence = min(spam_score, 1.0)
        
        return SpamAnalysisResult(
            is_spam=is_spam,
            confidence=confidence,
            reasons=reasons
        )
    
    def _is_suspicious_sender(self, email: str) -> bool:
        """Check if sender email looks suspicious."""
        # Random character patterns
        if re.search(r'[a-z]{1,2}\d{4,}@', email):
            return True
        
        # Too many numbers
        if len(re.findall(r'\d', email.split('@')[0])) > 4:
            return True
        
        # Random character sequences
        if re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', email.split('@')[0]):
            return True
        
        return False
    
    def _analyze_content(self, content: str) -> float:
        """Analyze email content for spam indicators."""
        content_lower = content.lower()
        score = 0.0
        
        # Check for spam keywords in content
        keyword_matches = sum(1 for keyword in self.SPAM_KEYWORDS if keyword in content_lower)
        score += keyword_matches * 0.05
        
        # Check for excessive punctuation
        if content.count('!') > 3 or content.count('?') > 3:
            score += 0.1
        
        # Check for all caps words
        caps_words = len([word for word in content.split() if word.isupper() and len(word) > 2])
        if caps_words > 3:
            score += 0.15
        
        return min(score, 0.5)  # Cap content score contribution


class EmailTaskHandler(BaseTaskHandler):
    """Specialized handler for email management tasks."""
    
    def __init__(self, browser_controller: BrowserController, 
                 context_manager: ContextManager,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.browser_controller = browser_controller
        self.context_manager = context_manager
        self.element_locator = ElementLocator(browser_controller.driver)
        self.page_analyzer = PageAnalyzer(browser_controller.driver)
        self.spam_detector = SpamDetector()
        
        # Configuration
        self.max_emails_per_batch = config.get("max_emails_per_batch", 50) if config else 50
        self.spam_confidence_threshold = config.get("spam_confidence_threshold", 0.7) if config else 0.7
        self.auto_delete_spam = config.get("auto_delete_spam", False) if config else False
        
        # State tracking
        self.current_service: Optional[str] = None
        self.service_config: Optional[Dict[str, Any]] = None
        self.processed_emails: List[EmailMetadata] = []
    
    async def can_handle_task(self, task: Task) -> bool:
        """Check if this handler can process the given task."""
        task_lower = task.description.lower()
        email_keywords = [
            "email", "inbox", "spam", "delete emails", "organize emails",
            "clean inbox", "mail", "gmail", "outlook", "yahoo mail"
        ]
        
        return any(keyword in task_lower for keyword in email_keywords)
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute email management task."""
        logger.info(f"Starting email task execution: {task.description}")
        
        try:
            # Navigate to email service if needed
            await self._ensure_email_service_access(task)
            
            # Detect current email service
            current_url = await self.browser_controller.get_current_url()
            self.current_service = EmailServiceDetector.detect_service(current_url)
            
            if not self.current_service:
                raise ValueError(f"Unsupported email service at URL: {current_url}")
            
            self.service_config = EmailServiceDetector.get_service_config(self.current_service)
            logger.info(f"Detected email service: {self.current_service}")
            
            # Navigate to inbox
            await self._navigate_to_inbox()
            
            # Parse task requirements
            task_type, task_params = self._parse_email_task(task.description)
            
            # Execute specific email task
            if task_type == "spam_detection":
                result = await self._handle_spam_detection(task_params)
            elif task_type == "email_organization":
                result = await self._handle_email_organization(task_params)
            elif task_type == "inbox_cleanup":
                result = await self._handle_inbox_cleanup(task_params)
            else:
                result = await self._handle_general_email_task(task)
            
            # Update task status
            task.update_status(TaskStatus.COMPLETED)
            task.set_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Email task execution failed: {e}")
            task.set_error(str(e))
            return {"error": str(e), "processed_emails": len(self.processed_emails)}
    
    async def _ensure_email_service_access(self, task: Task) -> None:
        """Ensure we have access to an email service."""
        current_url = await self.browser_controller.get_current_url()
        
        # Check if we're already on an email service
        if EmailServiceDetector.detect_service(current_url):
            return
        
        # Try to determine email service from task description
        task_lower = task.description.lower()
        
        if "gmail" in task_lower:
            await self.browser_controller.navigate_to("https://mail.google.com")
        elif "outlook" in task_lower or "hotmail" in task_lower:
            await self.browser_controller.navigate_to("https://outlook.live.com")
        elif "yahoo" in task_lower:
            await self.browser_controller.navigate_to("https://mail.yahoo.com")
        else:
            # Default to Gmail
            await self.browser_controller.navigate_to("https://mail.google.com")
        
        # Wait for page to load
        await self.browser_controller.wait_for_page_load()
    
    async def _navigate_to_inbox(self) -> None:
        """Navigate to the inbox folder."""
        if not self.service_config:
            raise ValueError("No service configuration available")
        
        inbox_selectors = self.service_config["inbox_selectors"]
        
        for selector in inbox_selectors:
            try:
                inbox_element = await self.element_locator.find_element_by_selector(selector)
                if inbox_element:
                    await self.browser_controller.click_element(inbox_element)
                    await self.browser_controller.wait_for_page_load()
                    logger.info("Successfully navigated to inbox")
                    return
            except Exception as e:
                logger.debug(f"Inbox selector {selector} failed: {e}")
                continue
        
        logger.warning("Could not find inbox navigation element")
    
    def _parse_email_task(self, description: str) -> Tuple[str, Dict[str, Any]]:
        """Parse email task description to determine task type and parameters."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["spam", "junk", "unwanted"]):
            return "spam_detection", {"action": "detect_and_handle"}
        
        if any(keyword in description_lower for keyword in ["organize", "sort", "folder"]):
            return "email_organization", {"action": "organize"}
        
        if any(keyword in description_lower for keyword in ["clean", "delete", "remove"]):
            return "inbox_cleanup", {"action": "cleanup"}
        
        return "general", {"action": "analyze"}
    
    async def _handle_spam_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle spam detection and management."""
        logger.info("Starting spam detection task")
        
        # Read emails from inbox
        emails = await self._read_email_list()
        
        spam_emails = []
        processed_count = 0
        
        for email in emails[:self.max_emails_per_batch]:
            # Analyze for spam
            spam_result = self.spam_detector.analyze_email(email)
            
            if spam_result.is_spam and spam_result.confidence >= self.spam_confidence_threshold:
                spam_emails.append({
                    "email": email.to_dict(),
                    "spam_analysis": spam_result.to_dict()
                })
                
                # Auto-delete if configured
                if self.auto_delete_spam:
                    success = await self._delete_email(email)
                    if success:
                        logger.info(f"Auto-deleted spam email: {email.subject}")
                else:
                    # Mark as spam
                    success = await self._mark_as_spam(email)
                    if success:
                        logger.info(f"Marked as spam: {email.subject}")
            
            processed_count += 1
        
        return {
            "task_type": "spam_detection",
            "processed_emails": processed_count,
            "spam_emails_found": len(spam_emails),
            "spam_emails": spam_emails,
            "auto_deleted": self.auto_delete_spam
        }
    
    async def _handle_email_organization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle email organization tasks."""
        logger.info("Starting email organization task")
        
        # Read emails from inbox
        emails = await self._read_email_list()
        
        organized_count = 0
        organization_actions = []
        
        for email in emails[:self.max_emails_per_batch]:
            # Determine organization action based on email content
            action = self._determine_organization_action(email)
            
            if action and action != "keep_in_inbox":
                success = await self._execute_organization_action(email, action)
                if success:
                    organized_count += 1
                    organization_actions.append({
                        "email_subject": email.subject,
                        "action": action,
                        "success": success
                    })
        
        return {
            "task_type": "email_organization",
            "processed_emails": len(emails),
            "organized_emails": organized_count,
            "organization_actions": organization_actions
        }
    
    async def _handle_inbox_cleanup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inbox cleanup tasks."""
        logger.info("Starting inbox cleanup task")
        
        # Read emails from inbox
        emails = await self._read_email_list()
        
        deleted_count = 0
        cleanup_actions = []
        
        for email in emails[:self.max_emails_per_batch]:
            # Determine if email should be deleted
            should_delete = self._should_delete_email(email)
            
            if should_delete:
                success = await self._delete_email(email)
                if success:
                    deleted_count += 1
                    cleanup_actions.append({
                        "email_subject": email.subject,
                        "sender": email.sender,
                        "reason": "cleanup_criteria_met"
                    })
        
        return {
            "task_type": "inbox_cleanup",
            "processed_emails": len(emails),
            "deleted_emails": deleted_count,
            "cleanup_actions": cleanup_actions
        }
    
    async def _handle_general_email_task(self, task: Task) -> Dict[str, Any]:
        """Handle general email analysis tasks."""
        logger.info("Starting general email analysis task")
        
        # Read emails from inbox
        emails = await self._read_email_list()
        
        # Analyze emails for spam
        spam_analysis = []
        for email in emails[:self.max_emails_per_batch]:
            spam_result = self.spam_detector.analyze_email(email)
            spam_analysis.append({
                "email": email.to_dict(),
                "spam_analysis": spam_result.to_dict()
            })
        
        return {
            "task_type": "general_analysis",
            "processed_emails": len(emails),
            "email_analysis": spam_analysis,
            "service": self.current_service
        }
    
    async def _read_email_list(self) -> List[EmailMetadata]:
        """Read list of emails from current inbox view."""
        if not self.service_config:
            raise ValueError("No service configuration available")
        
        emails = []
        email_list_selectors = self.service_config["email_list_selectors"]
        
        # Find email list elements
        email_elements = []
        for selector in email_list_selectors:
            try:
                elements = await self.element_locator.find_elements_by_selector(selector)
                if elements:
                    email_elements = elements
                    break
            except Exception as e:
                logger.debug(f"Email list selector {selector} failed: {e}")
                continue
        
        if not email_elements:
            logger.warning("Could not find email list elements")
            return emails
        
        # Extract metadata from each email element
        for i, element in enumerate(email_elements[:self.max_emails_per_batch]):
            try:
                email_metadata = await self._extract_email_metadata(element, i)
                if email_metadata:
                    emails.append(email_metadata)
            except Exception as e:
                logger.debug(f"Failed to extract metadata from email {i}: {e}")
                continue
        
        logger.info(f"Successfully read {len(emails)} emails")
        return emails
    
    async def _extract_email_metadata(self, element, index: int) -> Optional[EmailMetadata]:
        """Extract metadata from a single email element."""
        try:
            # Get element selector for future reference
            element_selector = f"({self.service_config['email_list_selectors'][0]})[{index + 1}]"
            
            # Extract subject
            subject = await self._extract_text_from_element(
                element, self.service_config["email_subject_selectors"]
            ) or f"Email {index + 1}"
            
            # Extract sender
            sender_text = await self._extract_text_from_element(
                element, self.service_config["sender_selectors"]
            ) or "Unknown Sender"
            
            # Parse sender name and email
            sender_name, sender_email = self._parse_sender_info(sender_text)
            
            # Determine read status (simplified)
            is_read = await self._is_email_read(element)
            
            # Create metadata object
            return EmailMetadata(
                subject=subject.strip(),
                sender=sender_name,
                sender_email=sender_email,
                date=datetime.now(),  # Simplified - would extract actual date
                is_read=is_read,
                is_spam=False,  # Will be determined by analysis
                folder="inbox",
                element_selector=element_selector
            )
            
        except Exception as e:
            logger.error(f"Failed to extract email metadata: {e}")
            return None
    
    async def _extract_text_from_element(self, parent_element, selectors: List[str]) -> Optional[str]:
        """Extract text from child element using multiple selectors."""
        for selector in selectors:
            try:
                child_element = await self.element_locator.find_element_within_parent(
                    parent_element, selector
                )
                if child_element:
                    text = await self.browser_controller.get_element_text(child_element)
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue
        return None
    
    def _parse_sender_info(self, sender_text: str) -> Tuple[str, str]:
        """Parse sender name and email from sender text."""
        # Try to extract email from text like "John Doe <john@example.com>"
        email_match = re.search(r'<([^>]+)>', sender_text)
        if email_match:
            email = email_match.group(1)
            name = sender_text.replace(f"<{email}>", "").strip()
            return name or email.split('@')[0], email
        
        # Check if the text itself is an email
        if '@' in sender_text and '.' in sender_text:
            return sender_text.split('@')[0], sender_text
        
        # Default case
        return sender_text, f"{sender_text.lower().replace(' ', '')}@unknown.com"
    
    async def _is_email_read(self, element) -> bool:
        """Determine if an email is read based on visual indicators."""
        try:
            # Check for common "unread" indicators
            class_name = await self.browser_controller.get_element_attribute(element, "class")
            if class_name:
                # Gmail uses "zE" for unread, Outlook uses different classes
                unread_indicators = ["unread", "zE", "ms-font-weight-semibold"]
                return not any(indicator in class_name for indicator in unread_indicators)
            
            # Check for bold text (common unread indicator)
            font_weight = await self.browser_controller.get_element_css_property(element, "font-weight")
            if font_weight and (font_weight == "bold" or int(font_weight) > 400):
                return False  # Unread
            
            return True  # Default to read
            
        except Exception:
            return True  # Default to read if we can't determine
    
    def _determine_organization_action(self, email: EmailMetadata) -> Optional[str]:
        """Determine what organization action to take for an email."""
        subject_lower = email.subject.lower()
        sender_lower = email.sender.lower()
        
        # Newsletter/promotional emails
        if any(keyword in subject_lower for keyword in ["newsletter", "unsubscribe", "promotion", "deal"]):
            return "move_to_promotions"
        
        # Social media notifications
        if any(keyword in sender_lower for keyword in ["facebook", "twitter", "linkedin", "instagram"]):
            return "move_to_social"
        
        # Automated/system emails
        if any(keyword in sender_lower for keyword in ["noreply", "no-reply", "system", "automated"]):
            return "move_to_updates"
        
        # Keep important emails in inbox
        return "keep_in_inbox"
    
    def _should_delete_email(self, email: EmailMetadata) -> bool:
        """Determine if an email should be deleted during cleanup."""
        # Delete obvious spam
        spam_result = self.spam_detector.analyze_email(email)
        if spam_result.is_spam and spam_result.confidence > 0.8:
            return True
        
        # Delete old promotional emails
        subject_lower = email.subject.lower()
        if any(keyword in subject_lower for keyword in ["unsubscribe", "sale", "discount", "offer expires"]):
            return True
        
        # Delete emails from suspicious domains
        sender_domain = email.sender_email.split('@')[-1].lower()
        if any(suspicious in sender_domain for suspicious in SpamDetector.SUSPICIOUS_DOMAINS):
            return True
        
        return False
    
    async def _execute_organization_action(self, email: EmailMetadata, action: str) -> bool:
        """Execute an organization action on an email."""
        try:
            # Select the email first
            email_element = await self.element_locator.find_element_by_selector(email.element_selector)
            if not email_element:
                return False
            
            await self.browser_controller.click_element(email_element)
            
            # Execute action based on type
            if action.startswith("move_to_"):
                folder_name = action.replace("move_to_", "")
                return await self._move_email_to_folder(email, folder_name)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to execute organization action {action}: {e}")
            return False
    
    async def _move_email_to_folder(self, email: EmailMetadata, folder: str) -> bool:
        """Move an email to a specific folder."""
        # This is a simplified implementation
        # In practice, this would need service-specific folder navigation
        logger.info(f"Moving email '{email.subject}' to folder '{folder}'")
        return True  # Placeholder
    
    async def _mark_as_spam(self, email: EmailMetadata) -> bool:
        """Mark an email as spam."""
        try:
            # Select the email
            email_element = await self.element_locator.find_element_by_selector(email.element_selector)
            if not email_element:
                return False
            
            await self.browser_controller.click_element(email_element)
            
            # Find and click spam button
            spam_selectors = self.service_config["spam_selectors"]
            for selector in spam_selectors:
                try:
                    spam_button = await self.element_locator.find_element_by_selector(selector)
                    if spam_button:
                        await self.browser_controller.click_element(spam_button)
                        logger.info(f"Marked as spam: {email.subject}")
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to mark email as spam: {e}")
            return False
    
    async def _delete_email(self, email: EmailMetadata) -> bool:
        """Delete an email."""
        try:
            # Select the email
            email_element = await self.element_locator.find_element_by_selector(email.element_selector)
            if not email_element:
                return False
            
            await self.browser_controller.click_element(email_element)
            
            # Find and click delete button
            delete_selectors = self.service_config["delete_selectors"]
            for selector in delete_selectors:
                try:
                    delete_button = await self.element_locator.find_element_by_selector(selector)
                    if delete_button:
                        await self.browser_controller.click_element(delete_button)
                        logger.info(f"Deleted email: {email.subject}")
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete email: {e}")
            return False
    
    def get_processed_emails(self) -> List[Dict[str, Any]]:
        """Get list of processed emails."""
        return [email.to_dict() for email in self.processed_emails]
    
    def get_handler_status(self) -> Dict[str, Any]:
        """Get current handler status."""
        return {
            "handler_type": "email",
            "current_service": self.current_service,
            "processed_emails_count": len(self.processed_emails),
            "max_emails_per_batch": self.max_emails_per_batch,
            "spam_confidence_threshold": self.spam_confidence_threshold,
            "auto_delete_spam": self.auto_delete_spam
        }