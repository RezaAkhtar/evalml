from abc import abstractmethod

import featuretools as ft

from evalml.pipelines.components.transformers.transformer import Transformer
from evalml.utils import infer_feature_types


class _ExtractFeaturesWithTransformPrimitives(Transformer):

    hyperparameter_ranges = {}
    """{}"""

    def __init__(self, random_seed=0, **kwargs):
        self._columns = None
        self._features = None
        super().__init__(random_seed=random_seed, **kwargs)

    @property
    @classmethod
    @abstractmethod
    def _transform_primitives(cls):
        """Return the transform primitives extracted from this component."""

    @abstractmethod
    def _get_columns_to_transform(self, X):
        """Return the columns that the primitives will transform."""

    @abstractmethod
    def _get_feature_types_for_featuretools(self, X):
        """Get a mapping from column name to the feature tools type.

        This is needed for dfs. Hopefully, once the ww/ft integration is complete this will be redundant.
        """

    def _make_entity_set(self, X):
        X_to_transform = X[self._columns]

        # featuretools expects str-type column names
        X_to_transform.rename(columns=str, inplace=True)
        ft_variable_types = self._get_feature_types_for_featuretools(X)
        es = ft.EntitySet()
        es.entity_from_dataframe(
            entity_id="X",
            dataframe=X_to_transform,
            index="index",
            make_index=True,
            variable_types=ft_variable_types,
        )
        return es

    def fit(self, X, y=None):
        X = infer_feature_types(X)
        self._columns = self._get_columns_to_transform(X)
        if len(self._columns) == 0:
            return self

        es = self._make_entity_set(X)
        self._features = ft.dfs(
            entityset=es,
            target_entity="X",
            trans_primitives=self._transform_primitives,
            max_depth=1,
            features_only=True,
        )
        return self

    def transform(self, X, y=None):
        X_ww = infer_feature_types(X)
        if self._features is None or len(self._features) == 0:
            return X_ww

        es = self._make_entity_set(X_ww)
        features = ft.calculate_feature_matrix(features=self._features, entityset=es)

        features.set_index(X_ww.index, inplace=True)

        X_ww = X_ww.ww.drop(self._columns)
        for col in features:
            X_ww.ww[col] = features[col]

        all_created_columns = self._get_feature_provenance().values()
        to_categorical = {
            col: "Categorical"
            for feature_list in all_created_columns
            for col in feature_list
        }
        X_ww.ww.set_types(to_categorical)
        return X_ww

    @staticmethod
    def _get_primitives_provenance(features):
        provenance = {}
        for feature in features:
            input_col = feature.base_features[0].get_name()
            # Return a copy because `get_feature_names` returns a reference to the names
            output_features = [name for name in feature.get_feature_names()]
            if input_col not in provenance:
                provenance[input_col] = output_features
            else:
                provenance[input_col] += output_features
        return provenance

    def _get_feature_provenance(self):
        provenance = {}
        if self._columns:
            provenance = self._get_primitives_provenance(self._features)
        return provenance


class EmailFeaturizer(_ExtractFeaturesWithTransformPrimitives):
    """Transformer that can automatically extract features from emails.

    Arguments:
        random_seed (int): Seed for the random number generator. Defaults to 0.
    """

    name = "Email Featurizer"
    _transform_primitives = [
        ft.primitives.IsFreeEmailDomain,
        ft.primitives.EmailAddressToDomain,
    ]

    def _get_columns_to_transform(self, X):
        return list(X.ww.select("EmailAddress", return_schema=True).columns)

    def _get_feature_types_for_featuretools(self, X):
        return {
            col_name: ft.variable_types.EmailAddress.type_string
            for col_name in self._columns
        }


class URLFeaturizer(_ExtractFeaturesWithTransformPrimitives):
    """Transformer that can automatically extract features from URL.

    Arguments:
        random_seed (int): Seed for the random number generator. Defaults to 0.
    """

    name = "URL Featurizer"
    _transform_primitives = [
        ft.primitives.URLToTLD,
        ft.primitives.URLToDomain,
        ft.primitives.URLToProtocol,
    ]

    def _get_columns_to_transform(self, X):
        return list(X.ww.select("URL", return_schema=True).columns)

    def _get_feature_types_for_featuretools(self, X):
        return {
            col_name: ft.variable_types.URL.type_string for col_name in self._columns
        }