local transf = require "transf"
local ParamBuilder = require "parambuilder_v1_1"
local constructionutil = require "constructionutil"
local positionx = ParamBuilder.Slider("offsetx", _("offset x-axis"), ParamBuilder.rangeSymm(1, 0.01), 1 / 0.01, _("jrm_param_offsetx_tooltip"))
local model_icons = {
    #model_icons
}
local model_values = {
    #model_values
}
local assetmodel = ParamBuilder.IconButton("type_param", _("vehicle"), model_icons, model_values, 1, _("jrm_param_type_tooltip"))

function data()

    return {
        type = #asset_type,
        description = {
            name = _("mod_name"),
        },
        availability = {
            yearFrom = #year_from_wagon,
            yearTo = 0,
        },
        buildMode = "MULTI",
        categories = { #categories },
        order = -2046867593,
        skipCollision = true,
        autoRemovable = false,
        params = {
                #height_params
        },
        updateFn = function(params)
            #get_params
            local height = 0
            #rail_height
            local result = { }
            result.models = { }

            table.insert(result.models, {
                id = assetmodel.getValue(params),
                transf = constructionutil.rotateTransf(params, { 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, trax, 0, height, 1 }),
            })

            result.terrainAlignmentLists = { {
                                                 type = "EQUAL",
                                                 faces = { }
                                             } }

            return result
        end
    }

end