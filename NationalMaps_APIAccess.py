import requests
import os
import json

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
            if download_data:
                self.dataset_download(api_query_results, override_confirmation=override_confirmation)
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


    def dataset_download(self, list_of_dictionaries, override_confirmation = False):
        """Combines all the functions to preview the total size for the data as well as begin the dota download."""
        if not override_confirmation:
            file_num, file_size =  self._download_metrics(list_of_dictionaries=list_of_dictionaries)
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
            for download_url in list_of_dictionaries:
                path_to_download = os.path.join(self.output_folder, os.path.basename(download_url["downloadURL"]))
                print(f"Now downloading {os.path.basename(download_url['downloadURL'])}. "
                      f"Size: {int(download_url['sizeInBytes'] * 0.000001)} MB")
                download_contents = requests.get(download_url["downloadURL"]).content
                print(f"Files remaining: {download_progress}/ {len(list_of_dictionaries)}")
                with open(path_to_download, "wb") as f:
                    f.write(download_contents)
                self._log_downloads(download_url)
                download_progress += 1

    def _download_metrics(self, list_of_dictionaries):
        """Provides the total size of all the downloads that match the query and returns the number of files and the amount of
         space needed."""
        total_size = 0
        total_downloads = len(list_of_dictionaries)
        for dictionary in list_of_dictionaries:
            total_size += dictionary["sizeInBytes"]

        total_size_in_MB = total_size * 0.000001
        return total_downloads, total_size_in_MB


if __name__ == "__main__":
    extend = [-122.13467361371288,
               36.889434553147886,
               -121.88787120849683,
               37.021862403517886]
    nationalmaps_api = NationalMAP_API(wgsbbox=[minX,
                                                minY,
                                                maxX,
                                                maxY],
                                       data_output_folder=r"r",
                                       log_output_folder=r"")
    nationalmaps_api.search_dataset("Lidar Point Cloud (LPC)",
                                    dataset_start_year=2015,
                                    dataset_end_year=2022,
                                    download_data=True)
