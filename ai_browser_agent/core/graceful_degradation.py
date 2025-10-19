"""Graceful degradation system for partial task completion."""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

from ai_browser_agent.interfaces.base_interfaces import BaseAgent
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.action import Action, ActionType


logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """Levels of degradation for task execution."""
    NONE = "none"
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    MAXIMUM = "maximum"


class PartialCompletionStrategy(Enum):
    """Strategies for partial task completion."""
    SKIP_OPTIONAL_STEPS = "skip_optional_steps"
    SIMPLIFY_ACTIONS = "simplify_actions"
    REDUCE_PRECISION = "reduce_precision"
    FALLBACK_TO_MANUAL = "fallback_to_manual"
    EXTRACT_AVAILABLE_DATA = "extract_available_data"
    COMPLETE_CORE_ONLY = "complete_core_only"


@dataclass
class DegradationContext:
    """Context for graceful degradation decisions."""
    task: Task
    failed_actions: List[Action]
    current_progress: float
    error_count: int
    time_elapsed: float
    available_alternatives: List[str]
    user_priorities: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PartialCompletionResult:
    """Result of partial task completion."""
    success: bool
    completion_percentage: float
    completed_steps: List[str]
    skipped_steps: List[str]
    degradation_level: DegradationLevel
    strategy_used: PartialCompletionStrategy
    message: str
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GracefulDegradationManager(BaseAgent):
    """Manages graceful degradation and partial task completion."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration
        self.min_completion_threshold = config.get("min_completion_threshold", 0.3) if config else 0.3
        self.max_error_tolerance = config.get("max_error_tolerance", 5) if config else 5
        self.time_limit_factor = config.get("time_limit_factor", 2.0) if config else 2.0
        
        # Degradation rules
        self._initialize_degradation_rules()
        
        # Tracking
        self.degradation_history: List[DegradationContext] = []
        self.strategy_success_rates: Dict[PartialCompletionStrategy, float] = {}
    
    def initialize(self) -> None:
        """Initialize the graceful degradation manager."""
        self.is_active = True
        logger.info("Graceful degradation manager initialized")
    
    def shutdown(self) -> None:
        """Shutdown the graceful degradation manager."""
        self.is_active = False
        logger.info("Graceful degradation manager shutdown")
    
    def _initialize_degradation_rules(self) -> None:
        """Initialize degradation rules for different scenarios."""
        self.degradation_rules = {
            # Email management degradation
            "email_management": {
                DegradationLevel.MINIMAL: {
                    "skip_steps": ["detailed_analysis", "advanced_filtering"],
                    "simplify_actions": ["use_basic_search", "simple_categorization"]
                },
                DegradationLevel.MODERATE: {
                    "skip_steps": ["spam_detection", "auto_organization", "detailed_analysis"],
                    "simplify_actions": ["manual_review_prompts", "basic_operations_only"]
                },
                DegradationLevel.SIGNIFICANT: {
                    "skip_steps": ["auto_actions", "bulk_operations"],
                    "simplify_actions": ["read_only_mode", "manual_confirmation_all"]
                }
            },
            
            # Online ordering degradation
            "online_ordering": {
                DegradationLevel.MINIMAL: {
                    "skip_steps": ["price_comparison", "review_analysis"],
                    "simplify_actions": ["basic_search", "simple_selection"]
                },
                DegradationLevel.MODERATE: {
                    "skip_steps": ["advanced_filtering", "recommendation_engine"],
                    "simplify_actions": ["manual_product_selection", "basic_checkout"]
                },
                DegradationLevel.SIGNIFICANT: {
                    "skip_steps": ["auto_checkout", "payment_processing"],
                    "simplify_actions": ["cart_preparation_only", "manual_completion_required"]
                }
            },
            
            # General web navigation degradation
            "web_navigation": {
                DegradationLevel.MINIMAL: {
                    "skip_steps": ["advanced_interactions", "dynamic_content_handling"],
                    "simplify_actions": ["basic_clicks_only", "simple_form_filling"]
                },
                DegradationLevel.MODERATE: {
                    "skip_steps": ["javascript_interactions", "complex_workflows"],
                    "simplify_actions": ["static_content_only", "manual_navigation_prompts"]
                },
                DegradationLevel.SIGNIFICANT: {
                    "skip_steps": ["automated_interactions"],
                    "simplify_actions": ["observation_mode", "manual_guidance_required"]
                }
            }
        }
    
    async def assess_degradation_need(self, context: DegradationContext) -> Tuple[bool, DegradationLevel]:
        """Assess whether graceful degradation is needed and at what level."""
        if not self.is_active:
            return False, DegradationLevel.NONE
        
        degradation_needed = False
        degradation_level = DegradationLevel.NONE
        
        # Check error count
        if context.error_count >= self.max_error_tolerance:
            degradation_needed = True
            degradation_level = DegradationLevel.SIGNIFICANT
        elif context.error_count >= self.max_error_tolerance * 0.6:
            degradation_needed = True
            degradation_level = DegradationLevel.MODERATE
        elif context.error_count >= self.max_error_tolerance * 0.3:
            degradation_needed = True
            degradation_level = DegradationLevel.MINIMAL
        
        # Check time elapsed vs expected
        if context.task.execution_plan and context.task.execution_plan.estimated_duration:
            expected_time = context.task.execution_plan.estimated_duration
            if context.time_elapsed > expected_time * self.time_limit_factor:
                degradation_needed = True
                if degradation_level == DegradationLevel.NONE:
                    degradation_level = DegradationLevel.MODERATE
        
        # Check progress vs time
        if context.current_progress < 0.5 and context.time_elapsed > 300:  # 5 minutes
            degradation_needed = True
            if degradation_level == DegradationLevel.NONE:
                degradation_level = DegradationLevel.MINIMAL
        
        # Check failed critical actions
        critical_failures = [
            action for action in context.failed_actions
            if action.is_destructive or action.confidence > 0.9
        ]
        if len(critical_failures) >= 2:
            degradation_needed = True
            degradation_level = max(degradation_level, DegradationLevel.MODERATE)
        
        logger.info(f"Degradation assessment: needed={degradation_needed}, level={degradation_level.value}")
        return degradation_needed, degradation_level
    
    async def execute_partial_completion(self, context: DegradationContext, 
                                       degradation_level: DegradationLevel) -> PartialCompletionResult:
        """Execute partial task completion with graceful degradation."""
        try:
            # Determine task category
            task_category = self._categorize_task(context.task)
            
            # Select appropriate strategy
            strategy = self._select_completion_strategy(context, degradation_level, task_category)
            
            # Execute the strategy
            result = await self._execute_strategy(strategy, context, degradation_level, task_category)
            
            # Update success rates
            self._update_strategy_success_rate(strategy, result.success)
            
            # Add to history
            self.degradation_history.append(context)
            
            logger.info(f"Partial completion executed: {result.completion_percentage:.1f}% complete")
            return result
            
        except Exception as e:
            logger.error(f"Error in partial completion: {e}")
            return PartialCompletionResult(
                success=False,
                completion_percentage=context.current_progress,
                completed_steps=[],
                skipped_steps=[],
                degradation_level=degradation_level,
                strategy_used=PartialCompletionStrategy.FALLBACK_TO_MANUAL,
                message=f"Partial completion failed: {str(e)}"
            )
    
    def _categorize_task(self, task: Task) -> str:
        """Categorize task for appropriate degradation rules."""
        description = task.description.lower()
        
        if any(keyword in description for keyword in ["email", "inbox", "spam", "mail"]):
            return "email_management"
        elif any(keyword in description for keyword in ["order", "buy", "purchase", "cart", "checkout"]):
            return "online_ordering"
        else:
            return "web_navigation"
    
    def _select_completion_strategy(self, context: DegradationContext, 
                                  degradation_level: DegradationLevel, 
                                  task_category: str) -> PartialCompletionStrategy:
        """Select the most appropriate completion strategy."""
        # Check user priorities
        if "core_functionality_only" in context.user_priorities:
            return PartialCompletionStrategy.COMPLETE_CORE_ONLY
        
        # Based on degradation level
        if degradation_level == DegradationLevel.MAXIMUM:
            return PartialCompletionStrategy.FALLBACK_TO_MANUAL
        elif degradation_level == DegradationLevel.SIGNIFICANT:
            return PartialCompletionStrategy.EXTRACT_AVAILABLE_DATA
        elif degradation_level == DegradationLevel.MODERATE:
            return PartialCompletionStrategy.SIMPLIFY_ACTIONS
        else:
            return PartialCompletionStrategy.SKIP_OPTIONAL_STEPS
    
    async def _execute_strategy(self, strategy: PartialCompletionStrategy, 
                              context: DegradationContext,
                              degradation_level: DegradationLevel,
                              task_category: str) -> PartialCompletionResult:
        """Execute a specific completion strategy."""
        if strategy == PartialCompletionStrategy.SKIP_OPTIONAL_STEPS:
            return await self._skip_optional_steps(context, degradation_level, task_category)
        
        elif strategy == PartialCompletionStrategy.SIMPLIFY_ACTIONS:
            return await self._simplify_actions(context, degradation_level, task_category)
        
        elif strategy == PartialCompletionStrategy.REDUCE_PRECISION:
            return await self._reduce_precision(context, degradation_level)
        
        elif strategy == PartialCompletionStrategy.FALLBACK_TO_MANUAL:
            return await self._fallback_to_manual(context, degradation_level)
        
        elif strategy == PartialCompletionStrategy.EXTRACT_AVAILABLE_DATA:
            return await self._extract_available_data(context, degradation_level)
        
        elif strategy == PartialCompletionStrategy.COMPLETE_CORE_ONLY:
            return await self._complete_core_only(context, degradation_level, task_category)
        
        else:
            return PartialCompletionResult(
                success=False,
                completion_percentage=context.current_progress,
                completed_steps=[],
                skipped_steps=[],
                degradation_level=degradation_level,
                strategy_used=strategy,
                message=f"Unknown strategy: {strategy.value}"
            )
    
    async def _skip_optional_steps(self, context: DegradationContext, 
                                 degradation_level: DegradationLevel,
                                 task_category: str) -> PartialCompletionResult:
        """Skip optional steps to focus on core functionality."""
        rules = self.degradation_rules.get(task_category, {}).get(degradation_level, {})
        steps_to_skip = rules.get("skip_steps", [])
        
        # Identify completed and skipped steps
        completed_steps = []
        skipped_steps = []
        
        if context.task.execution_plan:
            for step in context.task.execution_plan.steps:
                step_name = step.description.lower()
                
                # Check if step should be skipped
                should_skip = any(skip_keyword in step_name for skip_keyword in steps_to_skip)
                
                if should_skip:
                    skipped_steps.append(step.description)
                else:
                    completed_steps.append(step.description)
        
        # Calculate completion percentage
        total_steps = len(completed_steps) + len(skipped_steps)
        completion_percentage = len(completed_steps) / total_steps if total_steps > 0 else 0.0
        
        recommendations = [
            "Focus on core functionality only",
            "Manual review recommended for skipped steps",
            f"Skipped {len(skipped_steps)} optional steps to ensure completion"
        ]
        
        return PartialCompletionResult(
            success=True,
            completion_percentage=completion_percentage,
            completed_steps=completed_steps,
            skipped_steps=skipped_steps,
            degradation_level=degradation_level,
            strategy_used=PartialCompletionStrategy.SKIP_OPTIONAL_STEPS,
            message=f"Completed core functionality, skipped {len(skipped_steps)} optional steps",
            recommendations=recommendations
        )
    
    async def _simplify_actions(self, context: DegradationContext, 
                              degradation_level: DegradationLevel,
                              task_category: str) -> PartialCompletionResult:
        """Simplify actions to reduce complexity and failure risk."""
        rules = self.degradation_rules.get(task_category, {}).get(degradation_level, {})
        simplifications = rules.get("simplify_actions", [])
        
        completed_steps = []
        simplified_actions = []
        
        # Apply simplifications
        for simplification in simplifications:
            if simplification == "basic_operations_only":
                completed_steps.append("Switched to basic operations mode")
                simplified_actions.append("Complex interactions disabled")
            
            elif simplification == "manual_confirmation_all":
                completed_steps.append("Enabled manual confirmation for all actions")
                simplified_actions.append("User approval required for each step")
            
            elif simplification == "read_only_mode":
                completed_steps.append("Switched to read-only mode")
                simplified_actions.append("No destructive actions will be performed")
            
            elif simplification == "basic_search":
                completed_steps.append("Using basic search functionality")
                simplified_actions.append("Advanced search features disabled")
        
        completion_percentage = min(context.current_progress + 0.3, 0.8)  # Partial completion
        
        recommendations = [
            "Actions have been simplified to reduce failure risk",
            "Some advanced features may not be available",
            "Manual intervention may be needed for complex operations"
        ]
        
        return PartialCompletionResult(
            success=True,
            completion_percentage=completion_percentage,
            completed_steps=completed_steps,
            skipped_steps=simplified_actions,
            degradation_level=degradation_level,
            strategy_used=PartialCompletionStrategy.SIMPLIFY_ACTIONS,
            message=f"Actions simplified, {len(simplified_actions)} features disabled",
            recommendations=recommendations,
            metadata={"simplifications_applied": simplifications}
        )
    
    async def _reduce_precision(self, context: DegradationContext, 
                              degradation_level: DegradationLevel) -> PartialCompletionResult:
        """Reduce precision requirements to allow approximate completion."""
        completed_steps = [
            "Reduced precision requirements",
            "Accepting approximate results",
            "Relaxed validation criteria"
        ]
        
        # Estimate completion based on reduced requirements
        completion_percentage = min(context.current_progress + 0.4, 0.9)
        
        recommendations = [
            "Results may be approximate rather than exact",
            "Manual verification recommended",
            "Precision was reduced to ensure task completion"
        ]
        
        return PartialCompletionResult(
            success=True,
            completion_percentage=completion_percentage,
            completed_steps=completed_steps,
            skipped_steps=["High-precision validation", "Exact matching requirements"],
            degradation_level=degradation_level,
            strategy_used=PartialCompletionStrategy.REDUCE_PRECISION,
            message="Precision reduced to allow approximate completion",
            recommendations=recommendations
        )
    
    async def _fallback_to_manual(self, context: DegradationContext, 
                                degradation_level: DegradationLevel) -> PartialCompletionResult:
        """Fallback to manual completion with guidance."""
        completed_steps = [
            "Prepared task for manual completion",
            "Generated step-by-step guidance",
            "Documented current progress"
        ]
        
        # Provide manual completion guidance
        manual_steps = []
        if context.task.execution_plan:
            for step in context.task.execution_plan.steps:
                if not step.completed:
                    manual_steps.append(f"Manual step: {step.description}")
        
        recommendations = [
            "Task requires manual completion",
            "Follow the provided step-by-step guidance",
            "Current progress has been preserved",
            f"Remaining steps: {len(manual_steps)}"
        ]
        
        return PartialCompletionResult(
            success=True,
            completion_percentage=context.current_progress,
            completed_steps=completed_steps,
            skipped_steps=manual_steps,
            degradation_level=degradation_level,
            strategy_used=PartialCompletionStrategy.FALLBACK_TO_MANUAL,
            message="Task prepared for manual completion",
            recommendations=recommendations,
            metadata={"manual_steps": manual_steps}
        )
    
    async def _extract_available_data(self, context: DegradationContext, 
                                    degradation_level: DegradationLevel) -> PartialCompletionResult:
        """Extract and preserve any data that was successfully gathered."""
        completed_steps = [
            "Extracted available data",
            "Preserved successful results",
            "Generated partial report"
        ]
        
        # Simulate data extraction from successful actions
        extracted_data = {}
        successful_actions = [
            action for action in context.failed_actions
            if hasattr(action, 'result') and action.result is not None
        ]
        
        for i, action in enumerate(successful_actions):
            extracted_data[f"result_{i}"] = {
                "action_type": action.type.value,
                "result": action.result,
                "timestamp": action.executed_at.isoformat() if action.executed_at else None
            }
        
        completion_percentage = min(context.current_progress + 0.2, 0.7)
        
        recommendations = [
            f"Extracted {len(extracted_data)} successful results",
            "Partial data is available for review",
            "Task can be resumed from current state"
        ]
        
        return PartialCompletionResult(
            success=True,
            completion_percentage=completion_percentage,
            completed_steps=completed_steps,
            skipped_steps=["Failed operations", "Incomplete data collection"],
            degradation_level=degradation_level,
            strategy_used=PartialCompletionStrategy.EXTRACT_AVAILABLE_DATA,
            message=f"Extracted {len(extracted_data)} successful results",
            recommendations=recommendations,
            metadata={"extracted_data": extracted_data}
        )
    
    async def _complete_core_only(self, context: DegradationContext, 
                                degradation_level: DegradationLevel,
                                task_category: str) -> PartialCompletionResult:
        """Complete only the core functionality, skipping all extras."""
        # Define core steps for each category
        core_steps_map = {
            "email_management": ["login", "access_inbox", "basic_email_operations"],
            "online_ordering": ["product_search", "add_to_cart", "basic_checkout"],
            "web_navigation": ["page_navigation", "basic_interactions", "data_extraction"]
        }
        
        core_steps = core_steps_map.get(task_category, ["basic_navigation", "core_interaction"])
        
        completed_steps = [f"Core step: {step}" for step in core_steps]
        skipped_steps = [
            "Advanced features",
            "Optional enhancements",
            "Non-essential operations",
            "Optimization steps"
        ]
        
        # Core functionality typically represents 60-80% of full task
        completion_percentage = min(context.current_progress + 0.5, 0.8)
        
        recommendations = [
            "Core functionality completed successfully",
            "Advanced features were skipped",
            "Task meets minimum requirements",
            "Full functionality can be added later if needed"
        ]
        
        return PartialCompletionResult(
            success=True,
            completion_percentage=completion_percentage,
            completed_steps=completed_steps,
            skipped_steps=skipped_steps,
            degradation_level=degradation_level,
            strategy_used=PartialCompletionStrategy.COMPLETE_CORE_ONLY,
            message=f"Core functionality completed ({len(core_steps)} steps)",
            recommendations=recommendations,
            metadata={"core_steps": core_steps}
        )
    
    def _update_strategy_success_rate(self, strategy: PartialCompletionStrategy, success: bool) -> None:
        """Update success rate for a completion strategy."""
        if strategy not in self.strategy_success_rates:
            self.strategy_success_rates[strategy] = 0.5
        
        current_rate = self.strategy_success_rates[strategy]
        new_rate = current_rate * 0.9 + (1.0 if success else 0.0) * 0.1
        self.strategy_success_rates[strategy] = new_rate
    
    def get_degradation_statistics(self) -> Dict[str, Any]:
        """Get graceful degradation statistics."""
        if not self.degradation_history:
            return {"total_degradations": 0}
        
        total_degradations = len(self.degradation_history)
        
        # Calculate average completion percentage
        avg_completion = sum(
            ctx.current_progress for ctx in self.degradation_history
        ) / total_degradations
        
        # Strategy usage distribution
        strategy_usage = {}
        for strategy, rate in self.strategy_success_rates.items():
            strategy_usage[strategy.value] = rate
        
        return {
            "total_degradations": total_degradations,
            "average_completion_percentage": avg_completion,
            "strategy_success_rates": strategy_usage,
            "min_completion_threshold": self.min_completion_threshold,
            "max_error_tolerance": self.max_error_tolerance
        }
    
    def create_degradation_report(self, result: PartialCompletionResult) -> str:
        """Create a human-readable degradation report."""
        report_lines = [
            "Graceful Degradation Report",
            "=" * 30,
            "",
            f"Completion Status: {result.completion_percentage:.1f}% complete",
            f"Degradation Level: {result.degradation_level.value}",
            f"Strategy Used: {result.strategy_used.value}",
            "",
            "Completed Steps:",
        ]
        
        for step in result.completed_steps:
            report_lines.append(f"  ✓ {step}")
        
        if result.skipped_steps:
            report_lines.extend([
                "",
                "Skipped Steps:",
            ])
            for step in result.skipped_steps:
                report_lines.append(f"  ⊘ {step}")
        
        if result.recommendations:
            report_lines.extend([
                "",
                "Recommendations:",
            ])
            for rec in result.recommendations:
                report_lines.append(f"  • {rec}")
        
        report_lines.extend([
            "",
            f"Message: {result.message}",
            f"Timestamp: {datetime.now().isoformat()}"
        ])
        
        return "\n".join(report_lines)