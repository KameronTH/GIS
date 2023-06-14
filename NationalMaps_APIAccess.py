import requests
import os
import json
import folium
import random
import geopandas as gpd
from geopandas import GeoSeries
from shapely.geometry import Polygon
import pandas as pd

class NationalMAP_API:
    """This class can be used to access the USGS National Maps API.
    The GUI site is provided here: https://apps.nationalmap.gov/downloader/"""
    def __init__(self, wgsbbox, data_output_folder, log_output_folder):
        self.website = r"https://tnmaccess.nationalmap.gov/api/v1/"
        self.output_folder = data_output_folder
        self.bbox = wgsbbox
        self.collection_year = None
        self.description = None
        self.data_url = None
        self.metadata = None
        self.dataset_name = None
        self.json_result = None
        self.log_output_folder = log_output_folder

    def search_dataset(self,
                       dataset_name,
                       dataset_start_year= 1990,
                       dataset_end_year = 2023,
                       data_type = "Publication",
                       download_data = False,
                       override_confirmation=False):
        """This method uses a dataset name and year provided by the user to identify and store entries that match
        the user's query."""
        if dataset_name.find(" ") != -1:
            api_dataset_name = self._spaces_handler(dataset_name)
        else:
            api_dataset_name = dataset_name
        availible_datasets = ["National Boundary Dataset (NBD)",
                              "National Elevation Dataset (NED) 1 meter",
                              "National Elevation Dataset (NED) 1 arc-second",
                              "Digital Elevation Model (DEM) 1 meter",
                              "Land Cover - Woodland",
                              "US Topo Historical",
                              "US Topo Current",
                              "National Elevation Dataset (NED) 1/3 arc-second - Contours",
                              "National Transportation Dataset (NTD)",
                              "Original Product Resolution (OPR) Digital Elevation Model (DEM)",
                              "Combined Vector",
                              "National Structures Dataset (NSD)",
                              "Small-scale Datasets - Transportation",
                              "Small-scale Datasets - Hydrology",
                              "Small-scale Datasets - Contours",
                              "Small-scale Datasets - Boundaries",
                              "Map Indices",
                              "USDA National Agriculture Imagery Program (NAIP)",
                              "National Watershed Boundary Dataset (WBD)",
                              "National Hydrography Dataset (NHD) Best Resolution",
                              "Historical Topographic Maps",
                              "Lidar Point Cloud (LPC)",
                              "Ifsar Orthorectified Radar Image (ORI)",
                              "Alaska IFSAR 5 meter DEM",
                              "National Elevation Dataset (NED) 1/9 arc-second",
                              "National Elevation Dataset (NED) Alaska 2 arc-second",
                              "National Elevation Dataset (NED) 1/3 arc-second",
                              "Ifsar Digital Surface Model (DSM)"
                              ]
        standardized_datasets = [self._spaces_handler(x).lower() for x in availible_datasets] # Rename datasets to correct url
        if api_dataset_name.lower() in standardized_datasets:
            start = f"&start={dataset_start_year}-08-01"
            end = f"&end={dataset_end_year}-08-31"
            date_datetype = f"&dateType={data_type}"
            bbox = f"&bbox={self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]}"
            dataset_query = f"datasets={api_dataset_name}"

            full_dataset = self.website + "products?" + dataset_query + date_datetype + start + end + bbox
            api_query_results = self._all_results(full_dataset)
            self.json_result = api_query_results
            if download_data:
                self.dataset_download(api_query_results, override_confirmation=override_confirmation)
                return api_query_results
            else:
                return api_query_results


        else:
            for i in availible_datasets:
                found_match = False
                if i.lower().find(dataset_name.lower()) != -1:
                    print(f"The name, {dataset_name}, seems to be incorrect. Did you mean to choose the "
                          f"dataset, {i}.")
                    found_match = True
                    break
            if not found_match:
                print(f"The dataset named, {dataset_name}, was not found in the list of available datasets")


    def _spaces_handler(self, query_text):
        """This method converts spaces in the query names to a form that's recognizable by the API"""
        if query_text.find(" ") != 1:
            handled_text = query_text.replace(" ", "%20")
            return handled_text
        else:
            return query_text

    def _all_results(self, api_url):
        """This function returns a list containing all posts that match the query. It does this by iterating through all
        results that are retrieved by the site."""
        full_results = []
        page_max = f"&max=200" #Total number of pages loaded
        offset_amount = 200 #How many entries to go through when loading a query
        get_dataset = requests.get(api_url + page_max)
        contents = get_dataset.json()
        full_results.append(contents)

        while contents["total"] > offset_amount:
            get_dataset = requests.get(api_url + page_max + f"&offset={offset_amount}")
            new_contents = get_dataset.json()
            full_results.append(new_contents)
            offset_amount += 200

        full_list = []
        for page in full_results:

            for item in page["items"]:
                full_list.append(item)

        return full_list #Returns the list of dictionaries that contain the data entries
    def _log_downloads(self, dict_item):
        """Creates a log for which files were downloaded through the API."""
        log_file = os.path.join(self.log_output_folder, "downloads_logs.json")
        if not os.path.exists(log_file):
            with open(log_file, "w") as f:
                json.dump([], f)
        with open(log_file, "r") as f:
            log = json.load(f)
            log.append(dict_item)
            with open(log_file, "w") as f:
                json.dump(log, f, indent=4)


    def dataset_download(self, api_query, override_confirmation = False):
        """Combines all the functions to preview the total size for the data as well as begin the dota download."""
        if not override_confirmation:
            file_num, file_size =  self._download_metrics(list_of_dictionaries=api_query)
            continue_download = input(f"You are about to download {file_num} datasets. The size of this download will be"
                                      f" {int(file_size)} MB or {int(file_size * 0.001)} GB. Would you still like to continue? (Y/N). ")
            if continue_download.lower() == "y":
                continue_download = True
            else:
                continue_download = False
        else:
            continue_download = True
        if continue_download:
            download_progress = 1
            for download_url in api_query:
                path_to_download = os.path.join(self.output_folder, os.path.basename(download_url["downloadURL"]))
                print(f"Now downloading {os.path.basename(download_url['downloadURL'])}. "
                      f"Size: {int(download_url['sizeInBytes'] * 0.000001)} MB")
                download_contents = requests.get(download_url["downloadURL"]).content
                print(f"Files remaining: {download_progress}/ {len(api_query)}")
                try:
                    with open(path_to_download, "wb") as f:
                        f.write(download_contents)
                    self._log_downloads(download_url)
                    download_progress += 1
                except Exception as e:
                    error_log = os.path.join(self.output_folder, "error_log.txt")
                    if not os.path.exists(error_log):
                        with open(error_log, "w"):
                            pass
                    with open(error_log, "a") as f:
                        f.write(f"The download for the entry, {download_url['title']} was not downloaded and was skipped. Here's the download link: {download_url['downloadURL']}.\n")
                   
    def _download_metrics(self, list_of_dictionaries):
        """Provides the total size of all the downloads that match the query and returns the number of files and the amount of
         space needed."""
        total_size = 0
        total_downloads = len(list_of_dictionaries)
        for dictionary in list_of_dictionaries:
            total_size += dictionary["sizeInBytes"]

        total_size_in_MB = total_size * 0.000001
        return total_downloads, total_size_in_MB

    def preview_query(self, save_preview_as_geojson = False):
        """This method provides a preview of the area that lidar will be downloaded for in a folium map, along with the
        option to store the preview's geometry, along with its associated attributes, to a geojson file. Uses query made
        by object"""

        user_extent = [ #Extent chosen by user
            [self.bbox[1], self.bbox[0]],
            [self.bbox[1], self.bbox[2]],
            [self.bbox[3], self.bbox[2]],
            [self.bbox[3], self.bbox[0]],
            [self.bbox[1], self.bbox[0]]
            ]
        # 0 = xmin | 1 = ymin | 2 = xmax | 3 = ymax

        preview_map = folium.Map([self.bbox[3], self.bbox[0]], zoom_start=12)
        def user_extent_preview():
            user_extent_polygon = folium.vector_layers.Rectangle(user_extent, **{"color": "red"})
            user_defined_group =folium.map.FeatureGroup(name="User Defined Extent", control=True) # Create folium Layergroup to toggle
            user_extent_polygon.add_to(user_defined_group)
            user_defined_group.add_to(preview_map)


        unique_publications = []
        for query in self.json_result: #Grab unique publications to group the polygons by
            publication_date = query["publicationDate"]
            unique_publications.append(publication_date)
        unique_publications = list(set(unique_publications))

        unique_pubDicts = []
        for unique_date in unique_publications: #Grab unique publications to group the polygons by
            date_query_dict = {"Unique Date": unique_date, "Matching Query": [], "Extent": []}
            for query in self.json_result:
                if unique_date == query["publicationDate"]:
                    query_extent = [
                        [query["boundingBox"]["minY"], query["boundingBox"]["minX"]],
                        [query["boundingBox"]["minY"], query["boundingBox"]["maxX"]],
                        [query["boundingBox"]["maxY"], query["boundingBox"]["maxX"]],
                        [query["boundingBox"]["maxY"], query["boundingBox"]["minX"]],
                        [query["boundingBox"]["minY"], query["boundingBox"]["minX"]]
                    ]
                    date_query_dict["Extent"].append(query_extent)
                    date_query_dict["Matching Query"].append(query)
            unique_pubDicts.append(date_query_dict)

        # Generate Folium group using dictionary
        for dictionary in unique_pubDicts:
            year = dictionary["Unique Date"]
            group_year = folium.map.FeatureGroup(name=year,
                                                 control=True)  # Create folium Layergroup to toggle
            def random_color():
                # code excerpt from geeksforgeeks Create random hex color
                color_options = ["green", "blue", "yellow", "orange", "purple", "grey", "black", "white"]
                color = random.choice(color_options)
                return color
            color = random_color()
            for extent, metadata in zip(dictionary["Extent"], dictionary["Matching Query"]):

                title = metadata["title"]
                actual_metadata = metadata["metaUrl"]
                data_download = metadata["downloadURL"]


                html = f"<p><b>Collection Name:</b>{title}</p><p><b>Data Source:</b>{data_download}</p><p><b>Metadata:</b>{actual_metadata}</p>"
                popup = folium.map.Popup(html=html, parse_html=False)

                result_rectangle = folium.vector_layers.Rectangle(extent, **{"color":color}, popup=popup)
                result_rectangle.add_to(group_year)
                group_year.add_to(preview_map)
        user_extent_preview()
        folium.LayerControl().add_to(preview_map)
        preview_map.save("test_map.html")
    def _save_preview_to_geodf(self):
        user_extent = [  # Extent chosen by user
            [self.bbox[0], self.bbox[1]],
            [self.bbox[2], self.bbox[1]],
            [self.bbox[2], self.bbox[3]],
            [self.bbox[0], self.bbox[3]],
            [self.bbox[0], self.bbox[1]]
        ]
        user_polygon = Polygon(user_extent)
        feature_polygons = []
        original_query = {
            "Title":[],
            "Metadata Url": [],
            "Publication Date":[],
            "Last Updated":[],
            "Date Created":[],
            "Vendor Data Url":[],
            "Download Url":[],
            "geometry":[]


        }
        for query in self.json_result:

            query_extent = [
                [query["boundingBox"]["minX"], query["boundingBox"]["minY"]],
                [query["boundingBox"]["minX"], query["boundingBox"]["maxY"]],
                [query["boundingBox"]["maxX"], query["boundingBox"]["maxY"]],
                [query["boundingBox"]["maxX"], query["boundingBox"]["minY"]],
                [query["boundingBox"]["minX"], query["boundingBox"]["minY"]]
            ]

            original_query["Title"].append(query["title"])
            original_query["Publication Date"].append(query["publicationDate"])
            original_query["Last Updated"].append(query["lastUpdated"])
            original_query["Date Created"].append(query["dateCreated"])
            original_query["Metadata Url"].append(query["metaUrl"])
            original_query["Vendor Data Url"].append(query["metaUrl"])
            original_query["Download Url"].append(query["downloadURL"])
            original_query["geometry"].append(Polygon(query_extent))

            feature_polygons.append(Polygon(query_extent))
        
        gdf = gpd.GeoDataFrame(data=original_query, geometry=original_query["geometry"],crs="EPSG:4326")
        #    original_query.append(query)
        # original_query_bbox = zip(original_query, feature_polygons)
        return gdf, GeoSeries(user_polygon, crs="EPSG:4326")


            


if __name__ == "__main__":
    import fiona
    print(fiona.supported_drivers)
    extent = [-122.13467361371288,
               36.889434553147886,
               -121.88787120849683,
               37.021862403517886]
    nationalmaps_api = NationalMAP_API(wgsbbox=[-122.13467361371288,
                                                36.889434553147886,
                                                -121.88787120849683,
                                                37.021862403517886],
                                       data_output_folder=r"",
                                       log_output_folder=r"")
    search_query = nationalmaps_api.search_dataset("Lidar Point Cloud (LPC)",
                                    dataset_start_year=2018,
                                    dataset_end_year=2022,
                                    download_data=False)
    
    # nationalmaps_api.preview_query()
    gdf, user_polygon, feature_polygon = nationalmaps_api._save_preview_to_geoseries()
    print(gdf)
    # nationalmaps_api.geoseries_to_geodf(user_poly = user_polygon, feature_poly = feature_polygon)
    # nationalmaps_api.create_geodf(feature_polygons=feature_polygon)