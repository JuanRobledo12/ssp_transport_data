from sklearn.linear_model import LinearRegression
import pandas as pd

class AirTransportFreight:

    def __init__(self, socioeconomic_vars_path, air_transport_data_path):
        self.socioeconomic_vars_path = socioeconomic_vars_path
        self.air_transport_data_path = air_transport_data_path

    def get_socioeconomic_vars_df(self):

        def load_data(file_path):
            return pd.read_csv(file_path)

        def merge_data(hist_df, proj_df, value_col):
            iso_alpha_3_codes = sorted(set(proj_df['iso_alpha_3'].values))
            years_all = range(min(hist_df['year'].values), max(proj_df['year'].values) + 1)
            data = []

            for iso_alpha_3 in iso_alpha_3_codes:
                for year in years_all:
                    try:
                        value = hist_df.loc[(hist_df['iso_alpha_3'] == iso_alpha_3) & (hist_df['year'] == year), value_col].values[0]
                    except IndexError:
                        value = proj_df.loc[(proj_df['iso_alpha_3'] == iso_alpha_3) & (proj_df['year'] == year), value_col].values[0]
                    data.append([iso_alpha_3, year, value])

            return pd.DataFrame(data, columns=['iso_alpha_3', 'year', value_col])

        # GDP
        df_gdp_hist = load_data(self.socioeconomic_vars_path['gdp_hist'])
        df_gdp_proj = load_data(self.socioeconomic_vars_path['gdp_proj'])
        df_gdp_all = merge_data(df_gdp_hist, df_gdp_proj, 'gdp_mmm_usd')

        # Rural population
        df_popru_hist = load_data(self.socioeconomic_vars_path['pop_rural_hist'])
        df_popru_proj = load_data(self.socioeconomic_vars_path['pop_rural_proj'])

        # Urban population
        df_popur_hist = load_data(self.socioeconomic_vars_path['pop_urban_hist'])
        df_popur_proj = load_data(self.socioeconomic_vars_path['pop_urban_proj'])

        df_popru_all = merge_data(df_popru_hist, df_popru_proj, 'population_gnrl_rural')
        df_popur_all = merge_data(df_popur_hist, df_popur_proj, 'population_gnrl_urban')

        # Merge population data
        df_pop_all = pd.merge(df_popur_all, df_popru_all, on=['iso_alpha_3', 'year'])

        # All Together
        iso_alpha_3_pop_gdp = sorted(set(df_pop_all['iso_alpha_3']).intersection(set(df_gdp_all['iso_alpha_3'])))
        years_all = range(min(df_popur_hist['year'].values), max(df_popur_proj['year'].values) + 1)
        c_y_pop_gdp = []

        for iso_alpha_3 in iso_alpha_3_pop_gdp:
            for year in years_all:
                pop_ur = df_pop_all.loc[(df_pop_all['iso_alpha_3'] == iso_alpha_3) & (df_pop_all['year'] == year), 'population_gnrl_urban'].values[0]
                pop_ru = df_pop_all.loc[(df_pop_all['iso_alpha_3'] == iso_alpha_3) & (df_pop_all['year'] == year), 'population_gnrl_rural'].values[0]
                gdp = df_gdp_all.loc[(df_gdp_all['iso_alpha_3'] == iso_alpha_3) & (df_gdp_all['year'] == year), 'gdp_mmm_usd'].values[0]
                c_y_pop_gdp.append([iso_alpha_3, year, pop_ur, pop_ru, gdp])

        df_pop_gdp_all = pd.DataFrame(c_y_pop_gdp, columns=['iso_alpha_3', 'year', 'population_gnrl_urban', 'population_gnrl_rural', 'gdp_mmm_usd'])
        
        return df_pop_gdp_all

    def merge_enduse_and_socioeconomic_vars(self, df_enduse, df_socioeconomic_vars, unique_iso_codes):
        
        years_all = range(min(df_socioeconomic_vars['year'].values), 2022)

        data = []
        for iso_alpha_3 in unique_iso_codes:
            for y in years_all:
                pop_ur = df_socioeconomic_vars.loc[(df_socioeconomic_vars['iso_alpha_3'] == iso_alpha_3) &
                                                   (df_socioeconomic_vars['year'] == y), 'population_gnrl_urban'].values[0]
                pop_ru = df_socioeconomic_vars.loc[(df_socioeconomic_vars['iso_alpha_3'] == iso_alpha_3) &
                                                   (df_socioeconomic_vars['year'] == y), 'population_gnrl_rural'].values[0]
                gdp = df_socioeconomic_vars.loc[(df_socioeconomic_vars['iso_alpha_3'] == iso_alpha_3) &
                                                (df_socioeconomic_vars['year'] == y), 'gdp_mmm_usd'].values[0]
                end_use = df_enduse.loc[(df_enduse['Country Code'] == iso_alpha_3), str(y)].values[0]

                if pd.notna(end_use) and float(end_use) != 0:
                    data.append([iso_alpha_3, y, pop_ur, pop_ru, gdp, float(end_use)])

        df_socioeconomic_enduse = pd.DataFrame(data, columns=['iso_alpha_3', 'year',
                                                              'population_gnrl_urban',
                                                              'population_gnrl_rural',
                                                              'gdp_mmm_usd',
                                                              'Aviation (mtkm)'])
        return df_socioeconomic_enduse

    def train_linear_model(self, df_socioeconomic_enduse):
        X = df_socioeconomic_enduse[['population_gnrl_urban', 'population_gnrl_rural', 'gdp_mmm_usd']]
        Y = df_socioeconomic_enduse['Aviation (mtkm)']

        linear_model = LinearRegression()
        linear_model.fit(X, Y)
        return linear_model

    def get_mean_air_transport_freight_df(self, df_socioeconomic_enduse):
        mean_df = df_socioeconomic_enduse.groupby('iso_alpha_3')['Aviation (mtkm)'].mean().reset_index()
        mean_df.columns = ['iso_alpha_3', 'Aviation_mean (mtkm)']
        return mean_df

    def get_aviation_freight_data(self):
        df_pop_gdp_all = self.get_socioeconomic_vars_df()
        df_enduse = pd.read_csv(self.air_transport_data_path, skiprows=[0, 1, 2])

        df_pop_gdp_all_iso_codes = df_pop_gdp_all['iso_alpha_3'].unique()
        enduse_iso_codes = df_enduse['Country Code'].unique()
        iso_alpha_3_codes = sorted(set(df_pop_gdp_all_iso_codes).intersection(set(enduse_iso_codes)))

        df_merged = self.merge_enduse_and_socioeconomic_vars(df_enduse, df_pop_gdp_all, iso_alpha_3_codes)
        linear_model = self.train_linear_model(df_merged)
        mean_df = self.get_mean_air_transport_freight_df(df_merged)

        years_hist = range(min(df_merged['year'].values), max(df_merged['year'].values) + 1)
        coun_year_dato = []

        for iso3 in iso_alpha_3_codes:
            for year in years_hist:
                if (iso3, year) in zip(df_merged['iso_alpha_3'].values, df_merged['year'].values):
                    mtkm = df_merged.loc[(df_merged['iso_alpha_3'] == iso3) & (df_merged['year'] == year), 'Aviation (mtkm)'].values[0]
                else:
                    try:
                        mtkm = mean_df.loc[mean_df['iso_alpha_3'] == iso3, 'Aviation_mean (mtkm)'].values[0]
                    except IndexError:
                        X_test = df_pop_gdp_all.loc[(df_pop_gdp_all['iso_alpha_3'] == iso3) & (df_pop_gdp_all['year'] == year)][['population_gnrl_urban', 'population_gnrl_rural', 'gdp_mmm_usd']]
                        mtkm = linear_model.predict(X_test)[0]
                    mtkm = max(mtkm, 0)
                coun_year_dato.append([iso3, year, mtkm])

        df_enduse_complete = pd.DataFrame(coun_year_dato, columns=['iso_alpha_3', 'year', 'Aviation (mtkm)'])

        return df_enduse_complete
