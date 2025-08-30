import sys,os
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from networksecurity.constants.training_pipeline import TARGET_COLUMN, DATA_TRANSFORMATION_IMPUTER_PARAMS
from networksecurity.entity.artifact_entity import DataTransformationArtifact, DataValidationArtifact
from networksecurity.entity.config_entity import DataTransformationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.utils.main_utils.utils import read_yaml_file, save_numpy_array_data, save_object

class DataTransformation:
    def __init__(self, data_validation_artifact: DataValidationArtifact,
                 data_transformation_config: DataTransformationConfig):
        try:
            logging.info(f"{'>>'*20}Data Transformation log started.{'<<'*20} ")
            self.data_validation_artifact: DataValidationArtifact = data_validation_artifact
            self.data_transformation_config: DataTransformationConfig = data_transformation_config
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def get_data_transformer_object(cls) -> Pipeline:
        try:
            logging.info(f"Creating data transformer object")
            imputer: KNNImputer = KNNImputer(**DATA_TRANSFORMATION_IMPUTER_PARAMS)
            processor: Pipeline = Pipeline([
                ('Imputer', imputer),
            ])
            return processor
        except Exception as e:
            raise NetworkSecurityException(e, sys)
    
    def initiate_data_transformation(self) -> DataTransformationArtifact:
            try:
                logging.info(f"Reading training and testing data")
                train_df = DataTransformation.read_data(self.data_validation_artifact.valid_train_file_path)
                test_df = DataTransformation.read_data(self.data_validation_artifact.valid_test_file_path)
                logging.info(f"Read train and test data completed")

                input_feature_train_df = train_df.drop(columns=[TARGET_COLUMN], axis=1)
                target_feature_train_df = train_df[TARGET_COLUMN]
                target_feature_train_df= target_feature_train_df.replace(-1, 0)

                input_feature_test_df = test_df.drop(columns=[TARGET_COLUMN], axis=1)
                target_feature_test_df = test_df[TARGET_COLUMN]
                target_feature_test_df= target_feature_test_df.replace(-1, 0)

                preprocessor = self.get_data_transformer_object()
                preprocessor_object = preprocessor.fit(input_feature_train_df)

                logging.info(f"Preprocessing object created and fit on training data")
                transformed_input_feature_train_df = preprocessor_object.transform(input_feature_train_df)
                transformed_input_feature_test_df = preprocessor_object.transform(input_feature_test_df)
                logging.info(f"Applying preprocessing object on training and testing datasets")

                train_arr = np.c_[transformed_input_feature_train_df, np.array(target_feature_train_df)]
                test_arr = np.c_[transformed_input_feature_test_df, np.array(target_feature_test_df)]

                save_numpy_array_data(file_path=self.data_transformation_config.transformed_train_file_path,
                                      array=train_arr)
                save_numpy_array_data(file_path=self.data_transformation_config.transformed_test_file_path,
                                      array=test_arr)
                save_object(file_path=self.data_transformation_config.transformed_object_file_path,
                            obj=preprocessor_object)
                logging.info(f"Saved transformed training and testing array")

                data_transformation_artifact = DataTransformationArtifact(
                    transformed_object_file_path = self.data_transformation_config.transformed_object_file_path,
                    transformed_train_file_path = self.data_transformation_config.transformed_train_file_path,
                    transformed_test_file_path = self.data_transformation_config.transformed_test_file_path,
                )
                return data_transformation_artifact

            except Exception as e:
                raise NetworkSecurityException(e, sys)