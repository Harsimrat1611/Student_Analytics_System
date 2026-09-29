from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression


def train_model(df):
    df['total'] = df[['math','science','english']].sum(axis=1)
    df['label'] = df['total'].apply(lambda x: 1 if x < 120 else 0)

    X = df[['math','science','english','attendance']]
    y = df['label']

    model = LogisticRegression()
    model.fit(X, y)

    return model


def predict_risk(model, df):
    X = df[['math','science','english','attendance']]
    return model.predict(X)