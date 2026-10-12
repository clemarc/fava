# R3 data model

LibraryRows: R2 RunRecord array sorted descending startDate, ascending UUID for ties;
no record cap and no source mutations. Source UUID is row identity and selection.
LibraryNotice: maps six R2 attempt states; saved collection/provenance is separate.
Saved [] has a previously loaded empty label; absent snapshot does not mean empty.
DistanceMode: device/kilometres/miles; initial device, UserDefaults retained mode.
DisplayUnit: kilometres/miles only, resolved each formatting operation; distance
source units/value remain untouched. Visible rounding increment 0.01 km or mi.
RunSelection: in-memory exact workout UUID and consumer callback, no details.
Root destination visibility: false on fresh launch; explicit open triggers one
read, native back resets destination. Sheet state is not a library entry.
