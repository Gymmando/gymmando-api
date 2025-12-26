"""
Workout Agent: Handles workout logging and retrieval.
"""

from datetime import datetime

from database.supabase_client import supabase
from graphs.types import GymmandoState


class WorkoutAgent:
    """Handles workout logging and retrieval."""

    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.saved_workouts = []
        self.pending_workout = None  # Store pending workout for confirmation
        self.collected_workout_data = {}  # Store collected data across multiple turns
        self._load_from_supabase()

    def _load_from_supabase(self):
        """Load existing workouts from Supabase for the current user."""
        if not supabase:
            return
        try:
            # Filter workouts by user_id
            response = supabase.table("workouts").select("*").eq("user_id", self.user_id).execute()
            if response.data:
                self.saved_workouts = response.data
                print(f"✅ Loaded {len(self.saved_workouts)} workouts from Supabase for user {self.user_id}")
        except Exception as e:
            print(f"⚠️  Error loading workouts: {e}")

    def _format_workout_summary(self, workout: dict) -> str:
        """Format workout data for confirmation message."""
        summary_parts = []
        summary_parts.append(f"**Muscle Group:** {workout.get('muscle_group', 'N/A').title()}")
        summary_parts.append(f"**Exercises:** {', '.join(workout.get('exercises', []))}")
        summary_parts.append(f"**Sets & Reps:** {workout.get('sets_reps', 'N/A')}")
        summary_parts.append(f"**Duration:** {workout.get('duration', 'N/A')}")
        summary_parts.append(f"**Rest Time:** {workout.get('rest_time', 'N/A')}")
        summary_parts.append(f"**Difficulty:** {workout.get('difficulty', 'N/A')}")
        if workout.get('notes'):
            summary_parts.append(f"**Notes:** {workout.get('notes')}")
        return "\n".join(summary_parts)

    def _save_to_supabase(self, workout: dict) -> bool:
        """Save workout to Supabase with user_id."""
        if not supabase:
            print("⚠️  Supabase not available, workout not persisted")
            return False
        try:
            # Ensure user_id is set
            workout["user_id"] = self.user_id
            # Don't set created_at manually - let database handle it with DEFAULT now()
            # workout["created_at"] = datetime.now().isoformat()
            
            print(f"🔍 Attempting to save workout: {workout}")
            response = supabase.table("workouts").insert(workout).execute()
            
            if response.data:
                print(f"💾 ✅ Saved workout '{workout['name']}' to Supabase for user {self.user_id}")
                print(f"📋 Workout ID: {workout.get('id')}")
                return True
            else:
                print(f"⚠️  No data returned from Supabase insert")
                return False
        except Exception as e:
            print(f"❌ Error saving workout: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

    async def execute(self, state: GymmandoState) -> GymmandoState:
        """Process workout-related requests."""
        # Check if there's a pending workout confirmation (stored in instance)
        if self.pending_workout:
            # User is responding to a confirmation request
            user_transcript_lower = state.get("transcript", "").lower()
            is_confirmation = any(word in user_transcript_lower for word in ["yes", "yeah", "yep", "correct", "right", "confirm", "save", "log it", "that's right", "ok", "okay"])
            
            if is_confirmation:
                # User confirmed - save the pending workout
                saved = self._save_to_supabase(self.pending_workout)
                if saved:
                    self.saved_workouts.append(self.pending_workout)
                    muscle_group = self.pending_workout.get("muscle_group", "")
                    state["response"] = f"✅ Logged your {muscle_group} workout! {', '.join(self.pending_workout.get('exercises', []))} - {self.pending_workout.get('sets_reps', '')}"
                    state["workout_data"] = {
                        "status": "success",
                        "message": f"✅ Logged your {muscle_group} workout!",
                        "workout": self.pending_workout,
                    }
                    self.pending_workout = None  # Clear pending workout
                    self.collected_workout_data = {}  # Clear collected data
                    return state
                else:
                    state["response"] = "❌ Failed to save workout. Please try again."
                    state["workout_data"] = {
                        "status": "error",
                        "message": "Failed to save workout",
                    }
                    return state
            else:
                # User said no or something else - ask what to change
                state["response"] = "No problem! What would you like to change?"
                state["workout_data"] = {
                    "status": "needs_correction",
                    "message": "User wants to change workout details",
                }
                self.pending_workout = None  # Clear pending workout
                self.collected_workout_data = {}  # Clear collected data
                return state
        
        intent = state.get("intent")
        if not intent:
            print("⚠️  No intent found in state")
            state["workout_data"] = {
                "status": "error",
                "message": "No intent found",
            }
            state["response"] = "I'm not sure what you mean. Try saying something like 'I did bench press'."
            return state
            
        intent_type = intent.get("type")
        data = intent.get("data", {})

        print(f"🏋️ Workout Agent: Handling '{intent_type}' for user {self.user_id}")
        print(f"🔍 Intent data: {data}")
        print(f"🔍 Previously collected data: {self.collected_workout_data}")

        if intent_type == "log_workout":
            # Merge new data with previously collected data
            # Update collected_data with any new information from this turn
            if data.get("exercises"):
                self.collected_workout_data["exercises"] = data.get("exercises", [])
            if data.get("muscle_group") and data.get("muscle_group") != "general":
                self.collected_workout_data["muscle_group"] = data.get("muscle_group")
            if data.get("sets"):
                self.collected_workout_data["sets"] = data.get("sets")
            if data.get("reps"):
                self.collected_workout_data["reps"] = data.get("reps")
            if data.get("weight"):
                self.collected_workout_data["weight"] = data.get("weight")
            if data.get("duration"):
                self.collected_workout_data["duration"] = data.get("duration")
            if data.get("rest_time"):
                self.collected_workout_data["rest_time"] = data.get("rest_time")
            if data.get("name"):
                self.collected_workout_data["name"] = data.get("name")
            if data.get("difficulty"):
                self.collected_workout_data["difficulty"] = data.get("difficulty")
            if data.get("notes"):
                self.collected_workout_data["notes"] = data.get("notes", "")
            
            # Use merged collected data
            collected_data = self.collected_workout_data.copy()
            
            # Extract values with defaults
            muscle_group = collected_data.get("muscle_group", "")
            exercises = collected_data.get("exercises", [])
            sets = collected_data.get("sets")
            reps = collected_data.get("reps")
            weight = collected_data.get("weight")
            duration = collected_data.get("duration")
            rest_time = collected_data.get("rest_time")
            notes = collected_data.get("notes", "")
            workout_name = collected_data.get("name", "")
            difficulty = collected_data.get("difficulty", "")
            
            # Check for missing ESSENTIAL information only
            missing_details = []
            
            # Required fields - only these are essential
            if not exercises or len(exercises) == 0:
                missing_details.append("exercises")
            
            if not muscle_group or muscle_group == "general":
                missing_details.append("muscle group")
            
            # Sets and reps (at least one should be provided)
            if not sets and not reps:
                missing_details.append("sets and reps")
            
            # Weight, duration, rest_time are OPTIONAL - use defaults if not provided
            
            # If we have missing details, return incomplete status
            if missing_details:
                # Ask for the FIRST missing detail (one at a time)
                first_missing = missing_details[0]
                
                # Build helpful prompt based on what's missing
                if first_missing == "exercises":
                    prompt = "What exercises did you do? For example: bench press, squats, or deadlifts."
                elif first_missing == "muscle group":
                    prompt = "What muscle group did you work? For example: chest, legs, or back."
                elif first_missing == "sets and reps":
                    prompt = "How many sets and reps did you do? For example: 3 sets of 10 reps."
                elif first_missing == "weight":
                    prompt = "What weight did you use? For example: 225 pounds or 100 kg."
                elif first_missing == "duration":
                    prompt = "How long did your workout take? For example: 45 minutes."
                elif first_missing == "rest time":
                    prompt = "What was your rest time between sets? For example: 60 seconds."
                else:
                    prompt = f"I need to know the {first_missing}."
                
                state["response"] = prompt
                state["workout_data"] = {
                    "status": "incomplete",
                    "message": prompt,
                    "missing_fields": missing_details,
                    "collected_data": collected_data,
                    "next_field_to_ask": first_missing,
                }
                return state

            # All required fields collected - prepare workout for confirmation
            muscle_group_lower = (collected_data.get("muscle_group") or "general").lower()
            
            # Build sets_reps string
            sets_reps_str = ""
            if collected_data.get("sets") and collected_data.get("reps"):
                sets_reps_str = f"{collected_data['sets']} sets of {collected_data['reps']} reps"
            elif collected_data.get("sets"):
                sets_reps_str = f"{collected_data['sets']} sets"
            elif collected_data.get("reps"):
                sets_reps_str = f"{collected_data['reps']} reps"
            else:
                sets_reps_str = "As performed"
            
            # Add weight if provided
            if collected_data.get("weight"):
                sets_reps_final = f"{sets_reps_str} @ {collected_data['weight']}"
            else:
                sets_reps_final = sets_reps_str

            # Generate workout ID
            existing_count = len(
                [
                    w
                    for w in self.saved_workouts
                    if w.get("muscle_group") == muscle_group_lower
                ]
            )
            workout_id = f"{muscle_group_lower}_custom_{existing_count + 1:03d}"

            # Create workout record with defaults for optional fields
            workout = {
                "id": workout_id,
                "name": collected_data.get("name") or f"{muscle_group_lower.title()} Session",
                "muscle_group": muscle_group_lower,
                "exercises": collected_data.get("exercises", []),
                "difficulty": collected_data.get("difficulty") or "Intermediate",
                "duration": collected_data.get("duration") or f"{len(collected_data.get('exercises', [])) * 10} minutes",
                "sets_reps": sets_reps_final,
                "rest_time": collected_data.get("rest_time") or "60-90 seconds",
                "notes": collected_data.get("notes", ""),
            }
            
            # Clear collected data after creating workout
            self.collected_workout_data = {}

            # First time we have all data - ask for confirmation
            # Store workout in instance for next turn
            self.pending_workout = workout
            summary = self._format_workout_summary(workout)
            state["response"] = f"Here's what I'm about to log:\n\n{summary}\n\nIs this correct? Say 'yes' to save it!"
            state["workout_data"] = {
                "status": "pending_confirmation",
                "message": "Here's what I'm about to log. Is this correct?",
                "workout": workout,
                "summary": summary,
            }
            return state

        elif intent_type == "view_workouts":
            muscle_group = data.get("muscle_group")
            if muscle_group:
                filtered = [
                    w
                    for w in self.saved_workouts
                    if w.get("muscle_group") == muscle_group.lower()
                ]
            else:
                filtered = self.saved_workouts

            if filtered:
                workout_list = "\n".join([
                    f"- {w.get('name', 'Workout')}: {', '.join(w.get('exercises', []))} ({w.get('sets_reps', 'N/A')})"
                    for w in filtered[:5]  # Show first 5
                ])
                state["response"] = f"Found {len(filtered)} workout(s):\n{workout_list}"
            else:
                state["response"] = "No workouts found. Start logging your workouts!"

            state["workout_data"] = {
                "status": "success",
                "message": f"Found {len(filtered)} workout(s)",
                "workouts": filtered,
            }

        else:
            # Handle general queries or unknown intents
            # If there's a pending workout, still check for confirmation
            if self.pending_workout:
                user_transcript_lower = state.get("transcript", "").lower()
                is_confirmation = any(word in user_transcript_lower for word in ["yes", "yeah", "yep", "correct", "right", "confirm", "save", "log it", "that's right", "ok", "okay"])
                if is_confirmation:
                    saved = self._save_to_supabase(self.pending_workout)
                    if saved:
                        self.saved_workouts.append(self.pending_workout)
                        muscle_group = self.pending_workout.get("muscle_group", "")
                        state["response"] = f"✅ Logged your {muscle_group} workout! {', '.join(self.pending_workout.get('exercises', []))} - {self.pending_workout.get('sets_reps', '')}"
                        state["workout_data"] = {
                            "status": "success",
                            "message": f"✅ Logged your {muscle_group} workout!",
                            "workout": self.pending_workout,
                        }
                        self.pending_workout = None
                        return state
            
            # No pending workout and not a workout intent - provide helpful response
            intent_type = intent.get("type", "unknown")
            if intent_type == "general_query":
                # Friendly response for general queries
                state["response"] = "Hey! I'm Gymmando, your workout tracking assistant. I can help you log your workouts - just tell me what exercises you did, like 'I did 3 sets of bench press'!"
            else:
                state["response"] = "I'm not sure what you mean. Try saying something like 'I did bench press' or 'show my workouts'."
            
            state["workout_data"] = {
                "status": "unknown",
                "message": "Not a workout request",
            }

        return state

