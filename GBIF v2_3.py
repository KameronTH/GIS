#How to use:
#This tool takes point data, summarizes the points within one or two polygon layers, and allows you to compare points
#that fall inside of a designated area. Proximity statistics are collected to indicate the distance of the nearest points from the area_Interest parameter.
#Note, as of now, all data needs to be in the same coordinate system.
#For incident folder, select GBIF simple csv file. For clip_Feature_class, select the feature that you will clip the layer by
#For projection, use a layer that contains desired projection data This will convert the projections of files within the target geodatabase
#area_Interest is the required polygon features for analysis. This parameter should be smaller than the feature class for overlap_area
#For overlap_area, assign a layer that is larger than the area_Interest parameter. These layers will be compared
import arcpy
import os
from arcpy import env
Default_Geodatabase = arcpy.GetParameterAsText(0)
env.workspace = Default_Geodatabase
env.overwriteOutput = True
#I recommend dividing this script into two parts with part 1 being used to extract GBIF files and reproject datasets within a geodatabase
#And part 2 which conducts the spatial joins for the features in question.
#Assign variables for user input
##raw_GBIF_spreadsheet =arcpy.GetParameterAsText(1)
clip_Feature_class = arcpy.GetParameterAsText(1)
projection = arcpy.GetParameterAsText(2)
area_Interest = arcpy.GetParameterAsText(3)
overlap_area = arcpy.GetParameterAsText(4)
Incident_Folder = arcpy.GetParameterAsText(5)
def GBIF_conversion(Default_Geodatabase, Incident_Folder,clip_Feature="",projection=""): #Projection is mandatory parameter but is last because of function order
    # This function converts simple csv files from GBIF to feature classes and stores them within an assigned geodatabase
    env.workspace = Default_Geodatabase
    env.overwriteOutput = True
    GBIF_Geodatabase = []
    GBIF_table = []
    for filename in os.listdir(Incident_Folder):
        print(filename)
        if filename.endswith(".csv"):
            print(filename)
            GBIF_table.append(Incident_Folder + "\\" + filename)
            GBIF_Geodatabase.append(Default_Geodatabase + "\\" + "PointData_" + filename)
            continue
        else:
            continue
    # Autoconvert GBIF Data from csv
    for file in GBIF_table:
        test_hyphen = file.find("-")
        if test_hyphen == -1:
            base_name = os.path.basename(file)
            new_feature_name = base_name
            rename_gdb = f"{new_feature_name[:-4]}_XY"
            print(file)
            print(base_name)
            print(f"Regular path: {rename_gdb}")
            print(f"Geodatabase path: {rename_gdb}")
            arcpy.management.XYTableToPoint(file, rename_gdb, "decimalLongitude",
                                            "decimalLatitude")
        else:
            base_name = os.path.basename(file)
            new_feature_name = base_name.replace('-', '')
            rename_gdb = f"{new_feature_name[:-4]}_XY"
            print(file)
            print(base_name)
            print(f"Regular path: {rename_gdb}")
            print(f"Geodatabase path: {rename_gdb}")
            arcpy.management.XYTableToPoint(file, rename_gdb, "decimalLongitude",
                                            "decimalLatitude")
    print(
        f"{rename_gdb} has been converted from a csv to a feature and is stored in the {Default_Geodatabase} folder.")
    # Elif statements are to prevent duplicating geoprocessing operations
    for feature in arcpy.ListFeatureClasses("*_XY"):
        features_extent = arcpy.Describe(feature).extent
        spatial_ref = arcpy.Describe(feature).spatialReference.name
        clipped_features = f"{feature}_clipped"
        feature_projection = arcpy.Describe(projection).spatialReference.name
        project_feature = f"{feature}_projected"
        if feature_projection == spatial_ref:
            clipped_features = feature
        else:
            arcpy.management.Project(feature, project_feature, projection,
                                     preserve_shape="PRESERVE_SHAPE")  # Later make coord user input, using a feature
        if clip_Feature == "":
            project_feature = project_feature  # Allows reprojection of feature without clipping
        elif features_extent == arcpy.Describe(clip_Feature).extent:
            project_feature = feature
            print(f"{clipped_features} is already in selected extent and has been skipped")
        else:
            arcpy.analysis.Clip(project_feature, clip_Feature, clipped_features)
    print(GBIF_table)
    print(GBIF_Geodatabase)
GBIF_conversion(Default_Geodatabase, Incident_Folder, clip_Feature=clip_Feature_class,projection=projection)
def feature_proj_clip(Default_Geodatabase,projection,clip_Feature=""):
#Reoccuring variables
    for feature in arcpy.ListFeatureClasses():
        features_extent = arcpy.Describe(feature).extent
        spatial_ref = arcpy.Describe(feature).spatialReference.name
        clipped_features = f"{feature}_clipped"
        feature_projection = arcpy.Describe(projection).spatialReference.name
        project_feature = f"{feature}_projected"
        clip_Feature = ""
        if feature_projection == spatial_ref:
            clipped_features = feature
            print(
                f"{clipped_features} is already in the selected projection and was only copied.")
        else:
            arcpy.management.Project(feature, project_feature, projection,
                                     preserve_shape="PRESERVE_SHAPE")
        if clip_Feature == "":
            project_feature = project_feature  # Allows reprojection of feature without clipping
        elif features_extent == arcpy.Describe(clip_Feature).extent:
            project_feature = feature
            print(f"{clipped_features} is already in selected extent and has been skipped")
        else:
            arcpy.analysis.Clip(project_feature, clip_Feature, clipped_features)
    feature_proj_clip(Default_Geodatabase,projection=projection,clip_Feature=clip_Feature_class)
def incident_union_poly(Default_Geodatabase,area_Interest, overlap_area=""):
    import arcpy
    from arcpy import env
    #Common variables that will be replaced with user input.
    env.workspace = Default_Geodatabase
    projection_1 = projection
    near_area = area_Interest
    print(type(near_area))
    print(near_area)
    Union_incident = []
    outFeature = ""
    incident_points =[]
    for point in arcpy.ListFeatureClasses(feature_type="Point"):
        if arcpy.Describe(near_area).spatialReference.name != arcpy.Describe(point).spatialReference.name:
            arcpy.management.Project(near_area, near_area + "_projected", point)
            print(f"The projection of the point layer,{near_area}, and the interest layer, {point} do not match, and the conflicting layer was converted to {projection}.")
            print(f"Features name {near_area}: Projection {arcpy.Describe(near_area).spatialReference.name}.")
            print(f"Features name {point}: Projection {arcpy.Describe(point).spatialReference.name}.")
            arcpy.analysis.Near(point, near_area)
        else:
            print(f"The wildcard made this {point}")
            arcpy.analysis.Near(point, near_area)
        if overlap_area == r"":
            noOverlap = area_Interest + "_" + point + "_union_noOverlap"
            arcpy.analysis.SpatialJoin(area_Interest, point, noOverlap)
            Union_incident.append(noOverlap)
        else:
            if arcpy.Describe(point).spatialReference.name == arcpy.Describe(overlap_area).spatialReference.name and arcpy.Describe(overlap_area).spatialReference.name == arcpy.Describe(area_Interest).spatialReference.name:
                layer_with_holes = "Union_Layer"
                Fill_holes_layer = overlap_area  # + "_projected_clipped"
                arcpy.analysis.PairwiseErase(Fill_holes_layer, area_Interest, layer_with_holes) #Makes layer containing missing cities
                # Make union of area of interest and overlap area
                inFeature = [[layer_with_holes, 0], [area_Interest, 1]]
                outFeature = area_Interest + "_Filled_Layer"
                arcpy.analysis.Union(inFeature, outFeature)
                Union_incident.append(point)
                # Perform spatial join for the product of union and incidents
                Union_incidents = Fill_holes_layer + "_FinalOutput"
                withOverlap = area_Interest + f"_{point}" + "_union_with_Overlap"
                arcpy.analysis.SpatialJoin(outFeature, point, withOverlap)
            else:
                print(
                f"The spatial projection for {point},{overlap_area},{area_Interest} are not the same, and the spatial join was not executed")
    for polygon in arcpy.ListFeatureClasses(wild_card="*_union_with_Overlap",feature_type="polygon"):
            arcpy.management.AddField(polygon, "Polygon_Type", "TEXT")
            Union_incidents_fields = arcpy.ListFields(polygon)
            for field in Union_incidents_fields:
                print(field.name)
            with arcpy.da.UpdateCursor(polygon, ["Polygon_Type", "FID_Union_Layer"]) as cursor:
                for row in cursor:
                    if row[1] == -1:
                        row[0] = "Interior Polygon"
                    else:
                        row[0] = "Exterior Polygon"
                    cursor.updateRow(row)
incident_union_poly(Default_Geodatabase, area_Interest, overlap_area)

