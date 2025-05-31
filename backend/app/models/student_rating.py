import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

from app.db.student_semesters import get_student_semesters

student_semesters = get_student_semesters()

# scoring model predicting user performance
# 0 - worst student, 0.5 - student performing as expected, 1 - best student
# goal: identify
# A student with a 4.0 GPA in easy classes gets a modest score.

# A student with a 3.7 GPA in hard classes, heavy course load, and tough grading can score higher.

# It accounts for difficulty, load, and performance variance — a multidimensional quality metric.

X = []
y = []


for semester in student_semesters:
    X.append([semester["semester"], semester["gpa"], semester["credits"], semester["semester_difficulty"], semester["delta_gpa"]])
    y.append(semester["score"])

X = np.array(X)
y = np.array(y)

# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)


regressor = RandomForestRegressor(n_estimators=10, random_state=42, oob_score=True)
regressor.fit(X, y)

oob_score = regressor.oob_score_
print(f'Out-of-Bag Score: {oob_score}')

predictions = regressor.predict(X)

mse = mean_squared_error(y, predictions)
print(f'Mean Squared Error: {mse}')

r2 = r2_score(y, predictions)
print(f'R-squared: {r2}')

