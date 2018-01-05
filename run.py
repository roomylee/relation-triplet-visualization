# -*- coding: utf-8 -*-

from flask import Flask, render_template, jsonify, request, Response
import mysql.connector as msc
import db_config

app = Flask(__name__)


config = db_config.connection_info

conn = msc.connect(**config)
qry = conn.cursor(buffered=True)


def get_triplet_json():
    query = "SELECT Subject, Object, Relation FROM relation"

    qry.execute(query)
    row = qry.fetchone()

    unique_nodes = set()
    edges = list()
    while row is not None:
        bac = row[0]
        dis = row[1]
        rel = row[2]

        unique_nodes.add(bac)
        unique_nodes.add(dis)
        unique_nodes.add(rel)

        # relation
        edges.append({"source": bac, "target": rel, "hidden": dis})
        edges.append({"source": dis, "target": rel, "hidden": bac})

        row = qry.fetchone()

    unique_nodes = sorted(unique_nodes)

    nodes = list()
    nodes_id = {}
    bac_count = 0
    dis_count = 0
    rel_count = 0
    for i, node in enumerate(unique_nodes):
        if node[:5] == "BAC00":
            nodes.append({"name": node, "type": "bacteria", "id": i})
            bac_count += 1
        elif node[:5] == "DIS00":
            nodes.append({"name": node, "type": "disease", "id": i})
            dis_count += 1
        else:
            nodes.append({"name": node, "type": "relation", "id": i})
            rel_count += 1

        nodes_id[node] = i

    for i, edge in enumerate(edges):
        edge["source"] = nodes_id[edge["source"]]
        edge["target"] = nodes_id[edge["target"]]
        edge["hidden"] = nodes_id[edge["hidden"]]
        edges[i] = edge

    unique_edges = {}
    for edge in edges:
        unique_edges[edge["source"]*1000000+edge["target"]*1000+edge["hidden"]] = edge
    unique_edges = list(unique_edges.values())

    graph = {"nodes": nodes, "links": unique_edges}

    return graph

# 메인 페이지 라우팅
@app.route('/')
def main():
    return render_template('index.html', triplet=get_triplet_json(), paper=paper)


paper = []

def get_entity_list():
    query = "SELECT Subject, Object, Relation FROM relation"

    qry.execute(query)
    row = qry.fetchone()

    bac = []
    dis = []
    rel = []
    while row is not None:
        bac.append(row[0])
        dis.append(row[1])
        rel.append(row[2])
        row = qry.fetchone()

    bac = list(sorted(set(bac)))
    dis = list(sorted(set(dis)))
    rel = list(sorted(set(rel)))

    return bac, dis, rel


def get_paper(bac, dis, rel):
    query = "SELECT sentence.sentence " \
            "FROM sentence, relation " \
            "where relation.SID=sentence.SID"

    if bac != "":
        query += " AND relation.Subject='" + bac + "'"
    if dis != "":
        query += " AND relation.Object='" + dis + "'"
    if rel != "":
        query += " AND relation.Relation='" + rel + "'"

    qry.execute(query)
    row = qry.fetchone()

    paper_list = []
    while row is not None:
        paper_list.append(row[0])
        row = qry.fetchone()

    print(paper_list)
    return paper_list

# 서치 페이지 라우팅
@app.route('/search')
def search():
    bac, dis, rel = get_entity_list()
    return render_template('search.html', triplet=get_triplet_json(), paper=paper,
                           bac_list=bac, rel_list=rel, dis_list=dis)


# 체크박스에 대한 ajax처리, 선택한 정치인에 대한 정보 받아옴.
@app.route('/search_paper', methods=["GET", "POST"])
def triplet():
    if request.method == 'POST':
        global paper
        print(request.json)
        paper = get_paper(request.json["bacteria"], request.json["disease"], request.json["relation"])
    return str(request.json)



# 실행
if __name__ == '__main__':
    app.run()
    #app.run(host="166.104.140.76", port=50000)
