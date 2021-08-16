from abc import abstractmethod

from evalml.pipelines.components.transformers import Transformer
from evalml.utils import infer_feature_types


class ColumnSelector(Transformer):
    """
    Initalizes an transformer that drops specified columns in input data.

    Arguments:
        columns (list(string)): List of column names, used to determine which columns to select.
        random_seed (int): Seed for the random number generator. Defaults to 0.
    """

    def __init__(self, columns=None, random_seed=0, **kwargs):
        if columns and not isinstance(columns, list):
            raise ValueError(
                f"Parameter columns must be a list. Received {type(columns)}."
            )

        parameters = {"columns": columns}
        parameters.update(kwargs)
        super().__init__(
            parameters=parameters, component_obj=None, random_seed=random_seed
        )

    def _check_input_for_columns(self, X):
        cols = self.parameters.get("columns") or []
        column_names = X.columns

        missing_cols = set(cols) - set(column_names)
        if missing_cols and len(cols) > 0:
            raise ValueError("Columns {cols} not found in input data.")

    @abstractmethod
    def _modify_columns(self, cols, X, y=None):
        """How the transformer modifies the columns of the input data."""

    def fit(self, X, y=None):
        """Fits the transformer by checking if column names are present in the dataset.

        Arguments:
            X (pd.DataFrame): Data to check.
            y (pd.Series, optional): Targets.

        Returns:
            self
        """
        X = infer_feature_types(X)
        self._check_input_for_columns(X)
        return self

    def transform(self, X, y=None):
        X = infer_feature_types(X)
        self._check_input_for_columns(X)
        cols = self.parameters.get("columns") or []
        modified_cols = self._modify_columns(cols, X, y)
        return infer_feature_types(modified_cols)


class DropColumns(ColumnSelector):
    """
    Drops specified columns in input data.

    Arguments:
        columns (list(string)): List of column names, used to determine which columns to drop.
        random_seed (int): Seed for the random number generator. Defaults to 0.
    """

    name = "Drop Columns Transformer"
    hyperparameter_ranges = {}
    """{}"""
    needs_fitting = False

    def _modify_columns(self, cols, X, y=None):
        return X.ww.drop(cols)

    def transform(self, X, y=None):
        """Transforms data X by dropping columns.

        Arguments:
            X (pd.DataFrame): Data to transform.
            y (pd.Series, optional): Targets.

        Returns:
            pd.DataFrame: Transformed X.
        """
        return super().transform(X, y)


class SelectColumns(ColumnSelector):
    """
    Selects specified columns in input data.

    Arguments:
        columns (list(string)): List of column names, used to determine which columns to select.
        random_seed (int): Seed for the random number generator. Defaults to 0.
    """

    name = "Select Columns Transformer"
    hyperparameter_ranges = {}
    """{}"""
    needs_fitting = False

    def _modify_columns(self, cols, X, y=None):
        return X.ww[cols]

    def transform(self, X, y=None):
        """Transforms data X by selecting columns.

        Arguments:
            X (pd.DataFrame): Data to transform.
            y (pd.Series, optional): Targets.

        Returns:
            pd.DataFrame: Transformed X.
        """
        return super().transform(X, y)


class SelectByType(ColumnSelector):
    """
    Selects columns by specified Woodwork logical type or semantic tag in input data.

    Arguments:
        column_types (string, ww.LogicalType, list(string), list(ww.LogicalType)): List of Woodwork types or tags, used to determine which columns to select.
        random_seed (int): Seed for the random number generator. Defaults to 0.
    """

    name = "Select Columns By Type Transformer"
    hyperparameter_ranges = {}
    """{}"""
    needs_fitting = False

    def __init__(self, column_types=None, random_seed=0, **kwargs):
        parameters = {"column_types": column_types}
        parameters.update(kwargs)
        Transformer.__init__(
            Transformer,
            parameters=parameters,
            component_obj=None,
            random_seed=random_seed,
        )

    def _check_input_for_columns(self, X):
        col_types = self.parameters.get("column_types")
        if col_types and X.ww.select(col_types).empty:
            raise ValueError("Columns of type {column_types} not found in input data.")

    def _modify_columns(self, cols, X, y=None):
        return X.ww.select(cols)

    def transform(self, X, y=None):
        X = infer_feature_types(X)
        self._check_input_for_columns(X)
        cols = self.parameters.get("column_types") or []
        modified_cols = self._modify_columns(cols, X, y)
        return infer_feature_types(modified_cols)
