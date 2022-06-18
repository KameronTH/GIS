from shapely.geometry import Point
import pyproj
from ipyleaflet import Map, Marker, basemaps, basemap_to_tiles, Popup, AwesomeIcon
from ipywidgets import HTML


def availible_features(unique_features):
    """ Use this function to make a list of features of interest. Features must be in a list. Like movie showings at
    theaters in an area."""
    features_list = tuple(set([features.title() for features in unique_features]))
    return features_list


def neat_feature_naming(availible_features):
    """Produces a string with correct formatting for the list of availible features."""
    if isinstance(availible_features,tuple):
        availible_features = list(availible_features)
        availible_features[-1] = f"and {availible_features[-1]}"
        neat_format = ", ".join(availible_features)
    elif isinstance(availible_features, list):
        availible_features[-1] = f"and {availible_features[-1]}"
        neat_format = ", ".join(availible_features)
    return neat_format


def availible_locations_info(name, WGS_coordinates=[0, 0], unique_features=[], **locations):
    """Produces a dictionary containing information such as name and location of an area of interest. The feature should
    be present availibility_feature output. Dicts can be appended to a list. Can use last parameter for additional info
    like address or a location description"""
    locations = {}
    locations["Name"] = name
    locations["WGS Coordinates"] = WGS_coordinates
    locations["Features"] = unique_features
    return locations


def user_location():
    """Standardizes obtaining user location from a user input when given WGS84 Coordinates."""
    user_name = True
    while user_name:
        try:
            user_location = input("What are the WGS coordinates of your location?\n").replace(" ", "").split(",")
            user_location = [float(x) for x in user_location]
            return user_location
        except:
            if len(user_location) > 0:
                print(
                    f"The location, {','.join(user_location)}, that you inputted is invalid. Please enter your coordinates"
                    f" in a x,y format.")
            else:
                print(f"The location, {user_location[0]} , that you inputted is invalid. Please enter your coordinates"
                      f" in a x,y format.")


def location_reprojection(WGS_Location=[], projected_crs_ESPG=int):
    """Function assumes coordinates are from WGS84. This function reprojects a list containing WGS84 coordinates
    to a projection of your choice."""
    transformer_self = pyproj.Transformer.from_crs(4326, projected_crs_ESPG)
    transformed_location = transformer_self.transform(WGS_Location[0], WGS_Location[1])
    return transformed_location


def feature_interest(availible_feature):
    """Provides a way for user to input what amenity that they are interested in. Currently, the script can
    only handle one amenity at a time. """
    wanted_feature = input(
        f"The following amenities, {availible_feature} are availible at (insert variable for location type)"
        f" near your location. \nWhat is an amenity that you are interested in?")
    return wanted_feature


def selecting_location(feature_of_interest, feature_list, AOI_info):
    """This function looks at the amenities present in a dictionary of places, compiled using the availible_locations_info
    function to compare the amenities present in each item of the list of dictionaries to the amenity that the user
    selected. If the place has the amenities that the user wants, it returns a dictionary of that location."""
    if feature_of_interest.title() not in feature_list:
        print("You may have misspelled a name. Please check your spelling and try again.")
        while feature_of_interest.title() not in feature_list:
            feature_of_interest = input("Please try again:\n")

    for k, v in AOI_info.items():
        if k == "Features":
            for features in v:
                if features in feature_list:
                    matching_AOI = AOI_info
                    return matching_AOI


def aoi_distance(user_location_proj, confirmed_feature_loc_proj):
    """This script takes the projected coordinates of a list containing the user's projected coordinates and the
    location's projected coordinates to calculate the linear distance of the locations from the user."""
        dist_to_feature = Point(user_location_proj).distance(Point(confirmed_feature_loc_proj))
    dist_in_mi = round(dist_to_feature / 1609.344,2)
    return dist_in_mi
