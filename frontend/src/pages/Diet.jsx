import { useState } from 'react';
import './Diet.css';

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'];
const DIET_TYPES = [
  { value: 'balanced', label: 'Balanced' },
  { value: 'high_protein', label: 'High Protein' },
  { value: 'low_carb', label: 'Low Carb' },
  { value: 'vegetarian', label: 'Vegetarian' },
];

export default function Diet() {
  const [preferences, setPreferences] = useState({ calories: 2000, allergies: '', cuisine: 'any' });
  const [ingredients, setIngredients] = useState('');
  const [selectedMeals, setSelectedMeals] = useState(['breakfast', 'lunch', 'dinner']);
  const [dietType, setDietType] = useState('balanced');
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggleMeal = (meal) => {
    setSelectedMeals((prev) =>
      prev.includes(meal) ? prev.filter((m) => m !== meal) : [...prev, meal]
    );
  };

  const generatePlan = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/diet/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferences,
          ingredients: ingredients.split(',').map((i) => i.trim()).filter(Boolean),
          meal_types: selectedMeals,
          diet_type: dietType,
        }),
      });
      const data = await res.json();
      setPlan(data);
    } catch {
      alert('Failed to generate meal plan. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="diet-page">
      <h1 className="page-title">Personalized Diet Plan</h1>
      <p className="page-subtitle">
        Select your meals, nutrients, and available ingredients to get a custom plan with recipes.
      </p>

      <div className="diet-layout">
        <div className="diet-form card">
          <h3>Your Preferences</h3>

          <label>Diet Type</label>
          <select value={dietType} onChange={(e) => setDietType(e.target.value)}>
            {DIET_TYPES.map((d) => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>

          <label>Target Calories</label>
          <input
            type="number"
            value={preferences.calories}
            onChange={(e) => setPreferences({ ...preferences, calories: +e.target.value })}
          />

          <label>Allergies / Restrictions</label>
          <input
            type="text"
            placeholder="e.g. nuts, dairy"
            value={preferences.allergies}
            onChange={(e) => setPreferences({ ...preferences, allergies: e.target.value })}
          />

          <label>Cuisine Preference</label>
          <input
            type="text"
            placeholder="e.g. Indian, Mediterranean"
            value={preferences.cuisine}
            onChange={(e) => setPreferences({ ...preferences, cuisine: e.target.value })}
          />

          <label>Available Ingredients (comma-separated)</label>
          <textarea
            rows={3}
            placeholder="e.g. rice, chicken, spinach, eggs, tomatoes"
            value={ingredients}
            onChange={(e) => setIngredients(e.target.value)}
          />

          <label>Meals to Include</label>
          <div className="meal-checkboxes">
            {MEAL_TYPES.map((meal) => (
              <label key={meal} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedMeals.includes(meal)}
                  onChange={() => toggleMeal(meal)}
                />
                {meal.charAt(0).toUpperCase() + meal.slice(1)}
              </label>
            ))}
          </div>

          <button className="primary" onClick={generatePlan} disabled={loading || selectedMeals.length === 0}>
            {loading ? 'Generating...' : 'Generate Meal Plan'}
          </button>
        </div>

        <div className="diet-results card">
          <h3>Your Meal Plan</h3>
          {!plan ? (
            <p className="placeholder">Fill in your preferences and generate a plan.</p>
          ) : (
            <>
              {plan.total_nutrients && (
                <div className="nutrient-summary">
                  <span>Calories: {plan.total_nutrients.calories}</span>
                  <span>Protein: {plan.total_nutrients.protein}g</span>
                  <span>Carbs: {plan.total_nutrients.carbs}g</span>
                  <span>Fat: {plan.total_nutrients.fat}g</span>
                </div>
              )}

              <div className="meals-list">
                {plan.meals?.map((meal, i) => (
                  <div key={i} className="meal-card">
                    <div className="meal-header">
                      <span className="meal-type">{meal.type}</span>
                      <span className="meal-calories">{meal.calories} cal</span>
                    </div>
                    <h4>{meal.name}</h4>
                    <p className="meal-ingredients">
                      <strong>Ingredients:</strong> {meal.ingredients?.join(', ')}
                    </p>
                    <p className="meal-recipe">{meal.recipe}</p>
                    <div className="meal-macros">
                      P: {meal.protein}g | C: {meal.carbs}g | F: {meal.fat}g
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
