import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.svm import LinearSVR
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb

data = pd.read_csv('cost-of-living_rev1(25JAN2020).csv')
pd.set_option('display.max_columns', 500)
data.set_index('Unnamed: 0', inplace=True)
data = data._convert(numeric=True)

# Data completion
data = data.T
data_mean = data['Avg Data Scientist Salary (USD/annum)'].mean()
data.fillna(data_mean, inplace=True)
cor_matrix = data.corr()
cor_matrix_y = cor_matrix['Avg Data Scientist Salary (USD/annum)'].sort_values(ascending=False)
print(cor_matrix_y)
# Dropping irrelevant features
data.drop(['Apartment (3 bedrooms) in City Centre',
           'Apartment (3 bedrooms) Outside of Centre'], axis=1, inplace=True)
data = data.astype(np.int64)


def data_visualization(dataset):
    corr_matrix = dataset.corr()
    corr_matrix_y = corr_matrix['Avg Data Scientist Salary (USD/annum)'].sort_values(ascending=False)
    column = list(corr_matrix_y.index[:11])
    column.pop(0)
    j = 1
    for i in column:
        plt.figure(j)
        sns.relplot(x='Avg Data Scientist Salary (USD/annum)', y=i, data=dataset)
        j += 1


data_visualization(data)


# Separating labels and target
data_target = data['Avg Data Scientist Salary (USD/annum)']
data.drop('Avg Data Scientist Salary (USD/annum)', axis=1, inplace=True)

# Data splitting
x_train, x_test, y_train, y_test = train_test_split(data, data_target, test_size=0.25, random_state=42)

# Data scaling and feature reduction and classifier
sc = StandardScaler()
pca = PCA()
svr = LinearSVR()
xgboost = xgb.XGBRegressor(random_state=42, objective='reg:squarederror')

# Best feature selection
rf_class = RandomForestRegressor(random_state=42, n_estimators=400)
sel = SelectFromModel(rf_class)
sel.fit(x_train, y_train)
selected_feature = x_train.columns[(sel.get_support())]


# creating data to train with only important features
x_train = x_train.loc[:, x_train.columns.intersection(selected_feature)]
x_test = x_test.loc[:, x_test.columns.intersection(selected_feature)]
print('Y_train describe', y_train.describe())

# Pipeline
pipe = Pipeline(steps=[('sc', sc), ('xgb', xgboost)])

# Calculating CV
cv = 5

# Grid search
grid_param = {'xgb__n_estimators': [10, 100, 1000],
              'xgb__learning_rate': [0.001, 0.01, 0.1, 0.5, 1],
              }
grid_param_rf = {
                 'n_estimators': [10, 100, 1000]}

grid = GridSearchCV(rf_class, grid_param_rf, cv=cv, n_jobs=-1)
grid.fit(x_train, y_train)
print(grid.best_params_)
model = grid.best_estimator_
model.fit(x_train, y_train)
predict = model.predict(x_test)
print('R2 Score', r2_score(y_test, predict))
print('Mean squared error', np.sqrt(mean_squared_error(y_test, predict)))

# Plotting data feature importance
importance = model.feature_importances_
indices = np.argsort(importance)
plt.title('Feature Importances')
plt.barh(range(len(indices)), importance[indices], color='b', align='center')
plt.yticks(range(len(indices)), [x_train.columns[i] for i in indices])
plt.xlabel('Relative Importance')
plt.show()
